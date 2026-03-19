from app import app, db, Issue, User

def clear_data():
    with app.app_context():
        try:
            Issue.query.delete()
            User.query.filter(User.username != 'admin').delete()
            db.session.commit()
            print("Data cleared successfully")
        except Exception as e:
            print("Error clearing data:", e)

if __name__ == "__main__":
    clear_data()
