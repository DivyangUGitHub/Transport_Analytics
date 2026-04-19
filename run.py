"""
One-click launcher for the Transport Analytics Dashboard
"""

import subprocess
import sys
import os

def check_and_install_dependencies():
    """Check and install required packages"""
    required = ['streamlit', 'pandas', 'numpy', 'plotly', 'folium', 
                'streamlit-folium', 'scikit-learn', 'statsmodels', 'tensorflow']
    
    print("Checking dependencies...")
    for package in required:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    
    print("\n✅ All dependencies installed!")

def create_data_folder():
    """Create data folder if it doesn't exist"""
    if not os.path.exists('data'):
        os.makedirs('data')
        print("✓ Created 'data' folder")

def main():
    print("="*60)
    print("🚇 TRANSPORT ANALYTICS DASHBOARD")
    print("="*60)
    print("\nStarting the application...\n")
    
    # Setup
    create_data_folder()
    check_and_install_dependencies()
    
    # Run streamlit app
    print("\n🚀 Launching dashboard...")
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])

if __name__ == "__main__":
    main()