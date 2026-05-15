import subprocess
import sys
import os
from pathlib import Path

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
    
    groq_key = os.environ.get('GROQ_API_KEY')
    print("-" * 40)
    if groq_key:
        print(f"✅ GROQ_API_KEY: {groq_key[:15]}...{groq_key[-4:]}")
        print("🌐 Will use API mode (Llama-3-8B)")
    else:
        print("⚠️  No GROQ_API_KEY - Using local models")
        print("💡 Free key: console.groq.com/keys")
    print("-" * 40)

def main():
    print_banner()
    check_setup()
    
    print("\n🚀 STARTING APP...")
    print("📱 http://localhost:8501")
    print("📊 Watch terminal for detailed logs\n")
    
    app_path = Path(__file__).parent / "app" / "streamlit_app.py"
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path), "--server.port", "8501"])

if __name__ == '__main__':
    main()