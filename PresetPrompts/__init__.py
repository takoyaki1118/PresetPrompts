# PresetPrompts/__init__.py
import traceback

# Print a message to confirm the script is running during ComfyUI startup
print("Initializing PresetPrompts Node...")

try:
    from .preset_prompt import PresetPromptGenerator

    NODE_CLASS_MAPPINGS = {
        "PresetPromptGenerator": PresetPromptGenerator
    }

    NODE_DISPLAY_NAME_MAPPINGS = {
        "PresetPromptGenerator": "Preset Prompt Generator" # English display name
    }

    __all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']

    print("Successfully initialized PresetPrompts Node.")

except Exception as e:
    print(f"Error initializing PresetPrompts Node: {e}")
    traceback.print_exc() # Print detailed traceback for debugging
    # Ensure __all__ is still defined even on error to avoid ComfyUI load issues
    NODE_CLASS_MAPPINGS = {}
    NODE_DISPLAY_NAME_MAPPINGS = {}
    __all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']