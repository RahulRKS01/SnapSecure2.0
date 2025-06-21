from flask import session, flash, redirect, url_for
from bson.objectid import ObjectId

def get_user_data(db):
    """Fetch the current user's data from the database."""
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in to access your profile.", "error")
        return redirect(url_for('login'))
    return db["User"].find_one({"_id": ObjectId(user_id)})

def update_user_data(db, form_data):
    """Update the user's profile information in the database."""
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in to update your profile.", "error")
        return redirect(url_for('login'))

    db["User"].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {
            "first_name": form_data.get('first_name'),
            "last_name": form_data.get('last_name'),
            "email": form_data.get('email'),
            "address": form_data.get('address'),
            "description": form_data.get('description')
        }}
    )
    flash("Profile updated successfully.", "success")
    return redirect(url_for('profile'))