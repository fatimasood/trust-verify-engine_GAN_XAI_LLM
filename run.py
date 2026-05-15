import subprocess
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file BEFORE checking for keys
load_dotenv()

def print_banner():
    print("""
╔══════════════════════════════════════════════════════════╗
║   🛡️  TRUSTVERIFY ENGINE v2.0                           ║
║   Multi-Modal Trust Verification System                  ║
║   MS Research Project - 2026                             ║
║                                                          ║
║   ⚡ DUAL MODE:                                          ║
║   🌐 API Mode: Groq (Llama-3) - If key available        ║
║   💻 Local Mode: HuggingFace Models - Auto fallback      ║
║   📊 Stats Mode: Always available                       ║
╚══════════════════════════════════════════════════════════╝
    """)

def check_setup():
    print("🔍 CHECKING SETUP...")
    print("-" * 40)
    print(f"✅ Python: {sys.version.split()[0]}")
    
    deps = ['streamlit', 'torch', 'transformers', 'beautifulsoup4', 'duckduckgo_search']
    for dep in deps:
        try:
            __import__(dep)
            print(f"✅ {dep}")
        except:
            print(f"❌ {dep} - MISSING")
            print(f"   Installing {dep}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"   ✅ Installed")
    
    # Check for Groq key from .env
    groq_key = os.environ.get('GROQ_API_KEY')
    print("-" * 40)
    if groq_key and not groq_key.startswith('YOUR_') and groq_key.strip():
        # Mask the key for display
        masked_key = groq_key[:15] + "..." + groq_key[-4:] if len(groq_key) > 20 else "***"
        print(f"✅ GROQ_API_KEY found: {masked_key}")
        print("🌐 Will use API mode (Llama-3-70B)")
    else:
        print("⚠️  No valid GROQ_API_KEY found in .env file")
        print("💡 Add your key to .env: GROQ_API_KEY=gsk_your_key_here")
        print("💡 Free key: console.groq.com/keys")
    print("-" * 40)

def main():
    print_banner()
    check_setup()
    
    print("\n🚀 STARTING APP...")
    print("📱 http://localhost:8501")
    print("📊 Watch terminal for detailed logs\n")
    
    # Pass environment variables to Streamlit subprocess
    env = os.environ.copy()
    app_path = Path(__file__).parent / "app" / "streamlit_app.py"
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(app_path), "--server.port", "8501"],
        env=env
    )

if __name__ == '__main__':
    main()