# Logo Setup Instructions

## Step 1: Save the Logo Image
The logo image you have has been prepared for use in the system.

**Action needed:**
1. Right-click on the logo image (the Barangay Sto. Niño seal/circular logo)
2. Select "Save image as..." or "Save picture as..."
3. Navigate to: `d:\senior_health_system\static\images\`
4. Save the file as: `logo.png`

## Step 2: Verify Setup
The system is now configured to:
- Serve static files from the `static/` folder
- Display the logo on the **homepage** (top-right in navbar, next to Login/Register buttons)
- Display the logo on the **login page** (top of login form, above "Welcome Back")

## Step 3: Run the Application
```powershell
# Activate virtual environment (if not already activated)
.venv\Scripts\activate

# Run Flask
python app.py
```

Then open:
- **Homepage**: http://localhost:5000/
- **Login page**: http://localhost:5000/login

## File Structure
```
senior_health_system/
├── static/
│   └── images/
│       └── logo.png  ← Save the logo here
├── templates/
│   ├── index.html (updated with logo in navbar)
│   ├── login.html (updated with logo in header)
│   └── ... other templates
├── app.py (updated with static folder configuration)
└── ... other files
```

**✓ Setup Complete!** The logo will now appear in both locations automatically once you save the image file.
