#!/usr/bin/env python3
"""
Quick setup script for Multi-Agent AI Medical Analysis System
"""
import os
import shutil
import subprocess
import sys

def setup_project():
    """Setup the project for development"""
    print("🏥 Multi-Agent AI Medical Analysis System - Setup")
    print("=" * 50)
    
    # Check if .env exists
    if not os.path.exists('.env'):
        print("📝 Creating .env file from template...")
        if os.path.exists('.env.template'):
            shutil.copy('.env.template', '.env')
            print("✅ Created .env file")
            print("⚠️  Please edit .env file and add your API keys!")
        else:
            print("❌ .env.template not found")
            return False
    else:
        print("✅ .env file already exists")
    
    # Check if virtual environment exists
    if not os.path.exists('venv'):
        print("\n🐍 Creating virtual environment...")
        try:
            subprocess.run([sys.executable, '-m', 'venv', 'venv'], check=True)
            print("✅ Virtual environment created")
        except subprocess.CalledProcessError:
            print("❌ Failed to create virtual environment")
            return False
    else:
        print("✅ Virtual environment already exists")
    
    # Install requirements
    print("\n📦 Installing requirements...")
    try:
        if os.name == 'nt':  # Windows
            pip_path = os.path.join('venv', 'Scripts', 'pip')
        else:  # Unix/Linux/Mac
            pip_path = os.path.join('venv', 'bin', 'pip')
        
        subprocess.run([pip_path, 'install', '-r', 'requirements.txt'], check=True)
        print("✅ Requirements installed")
    except subprocess.CalledProcessError:
        print("❌ Failed to install requirements")
        return False
    
    # Setup database
    print("\n🗄️  Setting up database...")
    try:
        if os.name == 'nt':  # Windows
            python_path = os.path.join('venv', 'Scripts', 'python')
        else:  # Unix/Linux/Mac
            python_path = os.path.join('venv', 'bin', 'python')
        
        subprocess.run([python_path, 'setup_database.py'], check=True)
        print("✅ Database setup complete")
    except subprocess.CalledProcessError:
        print("❌ Failed to setup database")
        return False
    
    print("\n🎉 Setup complete!")
    print("\n📋 Next steps:")
    print("1. Edit .env file and add your API keys")
    print("2. Activate virtual environment:")
    if os.name == 'nt':  # Windows
        print("   venv\\Scripts\\activate")
    else:  # Unix/Linux/Mac
        print("   source venv/bin/activate")
    print("3. Run analysis: python main.py")
    print("4. View reports: python view_reports.py detailed")
    print("5. Start API: python start_api.py")
    
    return True

if __name__ == "__main__":
    success = setup_project()
    if not success:
        sys.exit(1)