import sqlite3
conn = sqlite3.connect('cardiosync_users.db')
cursor = conn.cursor()
cursor.execute('SELECT p.age, p.sex, p.bp_systolic, p.bp_diastolic, p.total_cholesterol, p.hdl, p.ldl, p.smoking, p.exercise_days, p.diet_quality, p.location, p.genomic_risk, p.genomic_genotypes, p.vcf_uploaded, p.updated_at, u.full_name FROM patient_data p JOIN users u ON p.user_id = u.user_id LIMIT 1')
row = cursor.fetchone()
print(row)
print(len(row))