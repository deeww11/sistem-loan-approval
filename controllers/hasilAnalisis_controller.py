from flask import Blueprint, render_template, session, redirect
from utils.db import get_db_connection
import math

hasil_bp = Blueprint('hasil', __name__)

def fuzzifikasi_cibil(x):
    sedang = 0
    tinggi = 0

    if 500 <= x <= 700:
        if x <= 600:
            sedang = (x - 500) / 100
        else:
            sedang = (700 - x) / 100

    if 600 <= x <= 900:
        if x <= 700:
            tinggi = (x - 600) / 100
        else:
            tinggi = (900 - x) / 200

    return "tinggi" if tinggi > sedang else "sedang"


def norm(val, min_val, max_val):
    return (val - min_val) / (max_val - min_val)


def distance(a, b):
    return round(math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(len(a)))), 4)


@hasil_bp.route('/hasil_analisis')
def hasil():

    if 'user' not in session:
        return redirect('/')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # ambil pengajuan
    cursor.execute("""
        SELECT * FROM pengajuan
        WHERE id_user=%s
        ORDER BY id_pengajuan DESC
        LIMIT 1
    """, (session['user'],))
    baru = cursor.fetchone()

    if not baru:
        cursor.close()
        conn.close()
        return "Belum ada data pengajuan"

    kategori = fuzzifikasi_cibil(baru['cibil_score'])

    # ambil kasus lama
    cursor.execute("""
        SELECT * FROM basis_kasus
        WHERE cibil_score=%s
    """, (kategori,))
    basis_kasus = cursor.fetchall()

    if not basis_kasus:
        cursor.close()
        conn.close()
        return "Data kasus kosong"

    # normalisasi data baru
    baru_norm = [
        norm(baru['no_of_dependents'], 0, 5),
        1 if baru['self_employed'] == "Yes" else 0,
        norm(baru['income_annum'], 300000, 9900000),
        norm(baru['loan_amount'], 900000, 37600000),
        norm(baru['loan_term'], 2, 20),
        norm(baru['cibil_score'], 300, 861)
    ]

    hasil = []

    for k in basis_kasus:
        lama_norm = [
            norm(k['no_of_dependents'], 0, 5),
            1 if k['self_employed'] == "Yes" else 0,
            norm(k['income_annum'], 300000, 9900000),
            norm(k['loan_amount'], 900000, 37600000),
            norm(k['loan_term'], 2, 20),
            norm(k['cibil_score'], 300, 861)
        ]

        d = distance(baru_norm, lama_norm)

        hasil.append({
            'id_kasus': k['id_kasus'],
            'distance': d,
            'keputusan': k['keputusan']
        })

    # similarity
    all_dist = [x['distance'] for x in hasil]
    dmin = min(all_dist)
    dmax = max(all_dist)

    for x in hasil:
        if dmax == dmin:
            x['similarity'] = 1
        else:
            sim = 1 - ((x['distance'] - dmin) / (dmax - dmin))
            x['similarity'] = round(sim, 4)

    # sorting
    hasil = sorted(hasil, key=lambda x: x['similarity'], reverse=True)

    # KNN
    n = len(hasil)
    k = max(1, int(math.sqrt(n)))

    topk = hasil[:k]

    approve = sum(1 for x in topk if x['keputusan'] == "Approve")
    reject = sum(1 for x in topk if x['keputusan'] == "Reject")

    mdm_approve = None
    mdm_reject = None

    if approve > reject:
        keputusan = "Approve"

    elif reject > approve:
        keputusan = "Reject"

    else:
        jarak_approve = [x['distance'] for x in topk if x['keputusan'] == "Approve"]
        jarak_reject = [x['distance'] for x in topk if x['keputusan'] == "Reject"]

        mdm_approve = sum(jarak_approve) / len(jarak_approve)
        mdm_reject = sum(jarak_reject) / len(jarak_reject)

        keputusan = "Reject" if mdm_reject > mdm_approve else "Approve"

    # simpan hasil
    cursor.execute("""
        UPDATE pengajuan
        SET keputusan=%s
        WHERE id_pengajuan=%s
    """, (keputusan, baru['id_pengajuan']))

    conn.commit()
    cursor.close()
    conn.close()

    return render_template(
        'hasil_analisis.html',
        ranking=hasil,
        topk=topk,
        keputusan=keputusan,
        k=k,
        mdm_approve=round(mdm_approve, 4) if mdm_approve else None,
        mdm_reject=round(mdm_reject, 4) if mdm_reject else None
    )