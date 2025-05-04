# PresetPrompts/preset_prompt.py
import os
import json
import random
import re
import traceback
from collections import OrderedDict # キーの順序をある程度保持するために使用

# --- Helper Function ---
# ... (変更なし) ...
def _parse_specific_choices(choices_str):
    """Helper function to parse comma or newline separated strings into a list."""
    if not choices_str or not choices_str.strip():
        return []
    items = re.split(r'\s*,\s*|\s*\n\s*', choices_str.strip())
    return [item.strip() for item in items if item.strip()]


# --- Load Preset Data & Dynamically Determine Categories ---
PRESETS = {}
PRESET_FILE_PATH = os.path.join(os.path.dirname(__file__), 'presets.json')
# このリストはJSONから動的に生成します
_AVAILABLE_CATEGORIES = [] # モジュールレベルで定義

try:
    if os.path.exists(PRESET_FILE_PATH):
        with open(PRESET_FILE_PATH, 'r', encoding='utf-8') as f:
            # OrderedDictを使用してキーの順序を（可能な限り）保持
            PRESETS = json.load(f, object_pairs_hook=OrderedDict)

            if "None" not in PRESETS:
                 PRESETS["None"] = OrderedDict([("_description", "Fallback None preset")])
            print(f"[PresetPrompts] Loaded {len(PRESETS)} presets from {PRESET_FILE_PATH}")

            # --- Dynamically determine available categories ---
            all_category_keys = set()
            # 全てのプリセット(None除く)を走査してカテゴリキーを収集
            for preset_name, data in PRESETS.items():
                # Noneプリセットや、予期せず辞書でないデータはスキップ
                if preset_name != "None" and isinstance(data, dict):
                    # アンダースコアで始まらないキーをカテゴリ候補とする
                    valid_keys = {key for key in data.keys() if not key.startswith('_')}
                    all_category_keys.update(valid_keys)

            # 順序をある程度定義するため、最初に登場した非Noneプリセットのキー順をベースにする
            ordered_categories = []
            first_preset_key_order = []
            for preset_name, data in PRESETS.items():
                if preset_name != "None" and isinstance(data, dict):
                     first_preset_key_order = [k for k in data.keys() if not k.startswith('_')]
                     break # 最初の有効なプリセットのキー順を取得したら抜ける

            # 取得した順序でカテゴリを追加
            added_keys = set()
            for key in first_preset_key_order:
                if key in all_category_keys:
                    ordered_categories.append(key)
                    added_keys.add(key)

            # 最初のプリセットに含まれていなかったカテゴリを残りに追加（例: アルファベット順）
            remaining_keys = sorted(list(all_category_keys - added_keys))
            ordered_categories.extend(remaining_keys)

            _AVAILABLE_CATEGORIES = ordered_categories # モジュールレベル変数に最終的なカテゴリリストを格納
            print(f"[PresetPrompts] Dynamically determined categories: {_AVAILABLE_CATEGORIES}")

    else:
        print(f"[PresetPrompts] Warning: Preset file not found at {PRESET_FILE_PATH}. Creating default 'None' preset.")
        PRESETS = {"None": OrderedDict([("_description", "Default None preset")])}
        _AVAILABLE_CATEGORIES = [] # カテゴリなし

except json.JSONDecodeError as e:
    print(f"[PresetPrompts] Error loading presets.json: {e}")
    traceback.print_exc()
    PRESETS = {"None": OrderedDict([("_description", "Error Loading Presets")])}
    _AVAILABLE_CATEGORIES = []
except Exception as e:
    print(f"[PresetPrompts] An unexpected error occurred loading presets: {e}")
    traceback.print_exc()
    PRESETS = {"None": OrderedDict([("_description", "Error Loading Presets")])}
    _AVAILABLE_CATEGORIES = []


# --- Node Class Definition ---
class PresetPromptGenerator:
    CATEGORY = "PresetPrompts"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "generate_preset_prompt"

    # PRESET_CATEGORY_ORDER はもう使いません (動的に決定するため)
    # PRESET_CATEGORY_ORDER = [...]

    @classmethod
    def INPUT_TYPES(cls):
        # PRESETS と _AVAILABLE_CATEGORIES はモジュールレベルでロード済み
        preset_names = list(PRESETS.keys())
        if not preset_names:
            preset_names = ["None"]

        # 基本的な必須入力を定義
        required = {
            "randomize_preset": ("BOOLEAN", {"default": False}),
            "preset_name": (preset_names,),
            "prefix_tags": ("STRING", {"multiline": True, "default": "masterpiece, best quality"}),
            "character": ("STRING", {"multiline": False, "default": ""}),
            "suffix_tags": ("STRING", {"multiline": True, "default": ""}),
            "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
        }

        # --- Dynamically add category toggle inputs based on _AVAILABLE_CATEGORIES ---
        print(f"[PresetPrompts] Generating inputs for categories: {_AVAILABLE_CATEGORIES}") # デバッグ用
        for category in _AVAILABLE_CATEGORIES: # モジュールレベルで決定したカテゴリリストを使用
            input_name = f"enable_{category}"
            # 対応するBOOLEAN入力をrequiredに追加
            required[input_name] = ("BOOLEAN", {"default": True}) # デフォルトで有効にする

        return {"required": required}

    # **** Use **kwargs to accept dynamically generated enable inputs ****
    def generate_preset_prompt(self, randomize_preset, preset_name,
                               prefix_tags, character, suffix_tags, seed,
                               **kwargs): # 固定のenable引数の代わりにkwargsを使用

        rng = random.Random(seed)
        prompt_parts = []

        # --- Determine the actual preset name to use ---
        actual_preset_name = preset_name
        if randomize_preset:
            available_presets = [name for name in PRESETS.keys() if name != "None"]
            if available_presets:
                actual_preset_name = rng.choice(available_presets)
                # print(f"[PresetPrompts] Randomly selected preset: {actual_preset_name}") # Optional debug log
            else:
                # print("[PresetPrompts] Warning: No presets for randomization. Using 'None'.") # Optional debug log
                actual_preset_name = "None"
        # print(f"[PresetPrompts] Using preset: {actual_preset_name}") # Optional debug log

        # --- Dynamically build the enable_flags dictionary from kwargs ---
        enable_flags = {}
        # Use the globally determined _AVAILABLE_CATEGORIES to know which flags to look for
        for category in _AVAILABLE_CATEGORIES: # モジュールレベルのカテゴリリストを使用
            enable_key = f"enable_{category}"
            # kwargsから対応する値を取得。なければデフォルトのTrueを使用
            # (INPUT_TYPESのデフォルト値と合わせる)
            enable_flags[category] = kwargs.get(enable_key, True)

        # 1. Add Prefix Tags
        prompt_parts.extend(_parse_specific_choices(prefix_tags))

        # 2. Add Character (if specified)
        if character and character.strip():
            prompt_parts.extend(_parse_specific_choices(character))

        # 3. Process Selected Preset
        selected_preset_data = PRESETS.get(actual_preset_name)

        if selected_preset_data and actual_preset_name != "None" and isinstance(selected_preset_data, dict):
            # Iterate through categories based on the dynamically determined order
            for category in _AVAILABLE_CATEGORIES: # モジュールレベルのカテゴリリストを使用
                # Check if this category is enabled via the dynamically built flags
                if enable_flags.get(category, False): # 安全のため .get() を使用
                    tag_options = selected_preset_data.get(category, []) # プリセットからこのカテゴリのタグを取得
                    # Ensure tag_options is a list before choosing
                    if isinstance(tag_options, list) and tag_options:
                        chosen_tag = rng.choice(tag_options)
                        if chosen_tag and isinstance(chosen_tag, str) and chosen_tag.strip(): # Ensure tag is a non-empty string
                             prompt_parts.append(chosen_tag.strip())
                    # elif not isinstance(tag_options, list):
                        # Optional: Log a warning if a category value isn't a list
                        # print(f"[PresetPrompts] Warning: Category '{category}' in preset '{actual_preset_name}' is not a list.")

        # 4. Add Suffix Tags
        prompt_parts.extend(_parse_specific_choices(suffix_tags))

        # 5. Combine and Clean
        ordered_unique_parts = []
        seen = set()
        for part in prompt_parts:
             stripped_part = part.strip()
             if stripped_part and stripped_part not in seen:
                  ordered_unique_parts.append(stripped_part)
                  seen.add(stripped_part)

        final_prompt = ", ".join(filter(None, ordered_unique_parts))
        final_prompt = re.sub(r'(,\s*){2,}', ', ', final_prompt)
        final_prompt = re.sub(r'^\s*,\s*|\s*,\s*$', '', final_prompt)

        return (final_prompt,)

# Ensure __init__.py correctly imports this class and defines mappings
# ( __init__.py は変更不要です )