import datetime

def format_timestamp(seconds: float):
    td = datetime.timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds_ = total_seconds % 60
    milliseconds = int(td.microseconds / 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds_:02d},{milliseconds:03d}"

def generate_viral_subtitles(video_path, output_srt_path, words_per_chunk=1, model_size="small"):
    """
    Generate VIZARD.AI STYLE karaoke subtitles.
    Format: Prev Word + [Highlighted Current Word] + Next Word
    
    model_size: "small" (Fast, uses faster-whisper) or "medium" (Accurate, uses openai-whisper).
    """
    print(f"🎙️ Generating VIZARD-STYLE karaoke subtitles ({model_size})...")
    
    all_words = []
    
    # --- 1. TRY FASTER-WHISPER (5x Faster) ---
    try:
        # Force fallback if user wants "Accurate" mode (medium)
        if model_size == "medium":
            raise ImportError("Accurate mode selected -> Use openai-whisper")

        # Check if faster-whisper is installed (Import check strictly)
        import faster_whisper
        print("   🚀 Using FASTER-WHISPER (INT8 Optimized on CPU)...")
        
        # Run on CPU with INT8
        # We wrap the model loading and transcription in a nested try/except
        # so execution falls through to the 'fallback' block on ANY error.
        try:
            # Use selected model size (e.g. 'small', 'large-v2') 
            # Note: 'medium' is handled by fallback block above
            model = faster_whisper.WhisperModel(model_size, device="cpu", compute_type="int8")
            segments, info = model.transcribe(video_path, word_timestamps=True, language="hi")
            
            # Flatten words
            for segment in segments:
                for w in segment.words:
                    all_words.append({
                        "word": w.word.strip(),
                        "start": w.start,
                        "end": w.end
                    })
        except Exception as fast_e:
            print(f"   ⚠️ faster-whisper crashed: {fast_e}. Falling back...")
            raise ImportError("Force Fallback") # Trigger outer fallback

    except (ImportError, Exception):
        # --- 2. FALLBACK TO OPENAI-WHISPER (Slow) ---
        print("   ⚠️ faster-whisper not found! Falling back to SLOW whisper (openai-whisper)...")
        print("   👉 Run: pip install faster-whisper to speed up by 5x")
        
        import whisper
        # Use medium model for balance
        model = whisper.load_model("medium")
        result = model.transcribe(video_path, language="hi", word_timestamps=True)
        
        for segment in result["segments"]:
            if "words" in segment and segment["words"]:
                for w in segment["words"]:
                    all_words.append({
                        "word": w["word"].strip(),
                        "start": w["start"],
                        "end": w["end"]
                    })
            else:
                # Fallback implementation for segments without word timestamps
                words_list = segment["text"].strip().split()
                duration = segment["end"] - segment["start"]
                time_per_word = duration / len(words_list) if len(words_list) > 0 else 0.5
                for i, w_text in enumerate(words_list):
                    start = segment["start"] + (i * time_per_word)
                    end = segment["start"] + ((i+1) * time_per_word)
                    all_words.append({
                        "word": w_text,
                        "start": start,
                        "end": end
                    })

    except Exception as e:
        print(f"❌ Transcription Error: {e}")
        return False

    if not all_words:
        print("❌ No words found in transcription!")
        return False

    print(f"   -> Processing {len(all_words)} words for Karaoke style...")
    
    # --- 3. GENERATE KARAOKE SEGMENTS ---
    karaoke_segments = []
    
    for i, w in enumerate(all_words):
        text_parts = []
        
        # Previous Word (Normal White)
        if i > 0:
            text_parts.append(all_words[i-1]["word"])
        
        # Current Word (Highlighted Yellow + Bold)
        current_word = f"<font color=\"#FFEE00\"><b>{w['word']}</b></font>"
        text_parts.append(current_word)
        
        # Next Word (Normal White)
        if i < len(all_words) - 1:
            text_parts.append(all_words[i+1]["word"])
        
        final_text = " ".join(text_parts)
        
        karaoke_segments.append({
            "start": w["start"],
            "end": w["end"],
            "text": final_text
        })

    # --- 4. OPTIMIZE TIMING (No Overlap) ---
    final_segments = []
    for i, seg in enumerate(karaoke_segments):
        # Ensure no overlap with next segment
        if i < len(karaoke_segments) - 1:
            next_start = karaoke_segments[i+1]["start"]
            # Adjusted end time: 0.05s buffer
            seg["end"] = min(seg["end"], next_start - 0.05)
        
        # Ensure minimum duration
        if seg["end"] - seg["start"] < 0.1:
            seg["end"] = max(seg["end"], seg["start"] + 0.1)
            
        final_segments.append(seg)
    
    # --- 5. WRITE SRT FILE ---
    try:
        with open(output_srt_path, "w", encoding="utf-8") as f:
            for i, seg in enumerate(final_segments):
                start_ts = format_timestamp(seg["start"])
                end_ts = format_timestamp(seg["end"])
                
                f.write(f"{i + 1}\n")
                f.write(f"{start_ts} --> {end_ts}\n")
                f.write(f"{seg['text']}\n\n")
        
        print(f"✅ Vizard-style subtitles saved: {len(final_segments)} segments")
        return True
    except Exception as e:
        print(f"❌ Error writing SRT: {e}")
        return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python subtitle_optimizer.py <video_path> <output_srt_path>")
        sys.exit(1)
    
    video_path = sys.argv[1]
    output_srt = sys.argv[2]
    
    generate_viral_subtitles(video_path, output_srt)
