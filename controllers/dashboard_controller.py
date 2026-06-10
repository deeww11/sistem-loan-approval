from flask import Blueprint, render_template, session, redirect
from utils.db import get_db_connection

dashboard = Blueprint('dashboard', __name__)

@dashboard.route('/dashboard')
def dashboard_page():

    if 'user' not in session:
        return redirect('/')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Total kasus
    cursor.execute(
        "SELECT COUNT(*) AS total FROM basis_kasus"
    )
    total = cursor.fetchone()['total']

    # Approved
    cursor.execute("""
        SELECT COUNT(*) AS approved
        FROM basis_kasus
        WHERE loan_status = 'Approved'
    """)
    approved = cursor.fetchone()['approved']

    # Rejected
    cursor.execute("""
        SELECT COUNT(*) AS rejected
        FROM basis_kasus
        WHERE loan_status = 'Rejected'
    """)
    rejected = cursor.fetchone()['rejected']

    pending = 0

    # Data chart
    cursor.execute("""
        SELECT
            MONTH(tanggal_masuk) AS bulan,
            COUNT(*) AS jumlah
        FROM basis_kasus
        GROUP BY MONTH(tanggal_masuk)
        ORDER BY MONTH(tanggal_masuk)
    """)

    hasil = cursor.fetchall()

    bulan_map = {
        1: "Januari",
        2: "Februari",
        3: "Maret",
        4: "April",
        5: "Mei",
        6: "Juni",
        7: "Juli",
        8: "Agustus",
        9: "September",
        10: "Oktober",
        11: "November",
        12: "Desember"
    }

    labels = []
    values = []

    for row in hasil:
        labels.append(bulan_map[row['bulan']])
        values.append(row['jumlah'])

    total_chart = sum(values)

    if total_chart == 0:
        percentages = []
    else:
        percentages = [
            (v / total_chart) * 360
            for v in values
        ]

    colors = [
        "#7372e7",
        "#6fd3cb",
        "#ff4f87",
        "#e7e56f",
        "#f39c12",
        "#9b59b6"
    ]

    # Ambil data user untuk foto profil
    cursor.execute("""
        SELECT id_user, nama, foto
        FROM users
        WHERE id_user = %s
    """, (session['user'],))

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        'dashboard.html',
        user=user,
        nama=session['nama'],
        total=total,
        approved=approved,
        rejected=rejected,
        pending=pending,
        labels=labels,
        values=values,
        percentages=percentages,
        colors=colors
    )