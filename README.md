# CivicConnect - Ghaziabad Civic Issue Tracker

A Flask-based web application for tracking and reporting civic issues in Ghaziabad, built for the Ghaziabad Hackathon.

## 🎯 Features

✅ **User Authentication** - Secure registration and login system  
✅ **GPS Photo Upload** - Auto-detect locality from image EXIF data  
✅ **Hall of Shame Dashboard** - RWA rankings by issue resolution performance  
✅ **8 Localities Coverage** - Vaishali, Indirapuram, Raj Nagar, and more  
✅ **Mobile Responsive** - Beautiful beige/orange theme  
✅ **Admin Panel** - Manage issues and track statistics  
✅ **Community Features** - Upvote issues to show support  

## 📁 Project Structure

```
civicconnect2.0/
├── app.py                 # Main Flask application
├── demo_data.py          # Generate 50 test issues
├── localities.json       # 8 localities with RWA details
├── requirements.txt      # Python dependencies
├── templates/            # HTML templates
│   ├── base.html        # Base template with navbar
│   ├── landing.html     # Landing page
│   ├── login.html       # Login page
│   ├── register.html    # Registration page
│   ├── dashboard.html   # Main dashboard
│   ├── report_issue.html # Issue reporting form
│   ├── issue_detail.html # Issue details page
│   ├── hall_of_shame.html # RWA rankings
│   ├── admin.html       # Admin panel
│   ├── 404.html         # Not found page
│   └── 500.html         # Server error page
├── static/
│   ├── css/
│   │   └── style.css    # Responsive styling
│   └── uploads/         # User-uploaded photos
└── civicconnect.db      # SQLite database (auto-created)
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Initialize Database & Demo Data

```bash
# Run the app (creates database)
python app.py

# In a new terminal, generate demo data
python demo_data.py
```

### 3. Start the Application

```bash
python app.py
```

The app will run at: **http://localhost:5000**

## 🔐 Demo Credentials

**Admin Account:**
- Username: `admin`
- Password: `admin123`

**Test User:**
- Username: `user1`
- Password: `password123`

## 📋 Routes

| Route | Description |
|-------|-------------|
| `/` | Landing page |
| `/register` | User registration |
| `/login` | User login |
| `/dashboard` | Main dashboard with issues |
| `/report-issue` | Report new civic issue |
| `/issue/<id>` | View issue details |
| `/hall-of-shame` | RWA rankings |
| `/admin` | Admin panel (admin only) |

## 🎨 Features in Detail

### GPS Photo Upload
- Upload images with GPS coordinates embedded
- System automatically detects your locality
- Falls back to manual selection if GPS not available

### Hall of Shame Dashboard
- Ranks RWAs by total issues, unresolved count, average severity
- Shows resolution rate and health score
- Displays RWA contact details for accountability

### Issue Categories
- Potholes/Road Damage
- Garbage/Waste
- Water Supply
- Electricity
- Streetlights
- Drainage/Waterlogging
- Noise Pollution
- Traffic

### Severity Levels
- 1 - Minor
- 2 - Low
- 3 - Medium (default)
- 4 - High
- 5 - Critical

## 📱 Mobile Responsive Design

The app uses a mobile-first approach with:
- Responsive grid layouts
- Touch-friendly buttons
- Optimized for phones, tablets, and desktops
- Beige/Orange color scheme for accessibility

## 🗄️ Database Models

### User
- username, email, password (hashed)
- is_admin flag
- created_at timestamp

### Issue
- title, description, category
- locality_id, GPS coordinates
- photo URL, severity (1-5)
- status (pending/assigned/resolved)
- upvotes counter
- reporter_id (user who reported)

## 🛠️ Customization

### Add More Localities
Edit `localities.json` and add new locality objects with:
- id, name, lat, lng
- rwa_name, rwa_contact, rwa_email
- severity_score

### Modify Colors
Update CSS variables in `static/css/style.css`:
```css
--primary-color: #FF8C42;     /* Orange */
--secondary-color: #F5DEB3;   /* Beige */
```

## 📊 Admin Dashboard Features

- Total issues count
- Pending vs resolved issues
- Registered users count
- Recent issues table
- Quick status updates
- Issue severity viewing

## 🔒 Security Features

- Password hashing with Werkzeug
- Session-based authentication
- Admin role protection
- CSRF protection ready
- File upload validation

## 💡 For Hackathon Pitch

This MVP demonstrates:
1. **User Engagement** - Community reporting and upvoting
2. **Data Visualization** - Hall of Shame RWA rankings
3. **Accountability** - Public tracking of civic issues
4. **Scalability** - Ready to add more features
5. **Usability** - Mobile-first responsive design

## 🧪 Testing

```bash
# Generate test data with 50 sample issues
python demo_data.py

# Issues are distributed across:
# - 8 localities
# - 8 categories
# - 3 status states (pending/assigned/resolved)
# - Severity levels 1-5
```

## 📈 Next Steps for Production

1. Add email notifications
2. Implement real map integration (Google Maps)
3. Add image compression
4. Set up proper email service
5. Add analytics and reporting
6. Implement caching
7. Deploy to cloud (Heroku, AWS, GCP)

## 📝 License

Built for Ghaziabad Hackathon 2026

## 👥 Support

For issues or questions, contact the development team.

---

**Ready to launch! 🚀**
