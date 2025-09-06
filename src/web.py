# Test pygame audio
try:
    pygame.mixer.init()
    print("✅ Pygame audio system working")
    pygame.mixer.quit()
except Exception as e:
    print(f"❌ Pygame audio issue: {e}")