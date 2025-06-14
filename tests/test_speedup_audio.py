import sys
import os
import subprocess
from pydub import AudioSegment


def get_audio_duration(filepath):
    audio = AudioSegment.from_file(filepath)
    return audio.duration_seconds

def build_atempo_filters(speed):
    """
    ffmpeg's atempo filter only supports values between 0.5 and 2.0.
    For larger/smaller values, chain multiple atempo filters.
    """
    filters = []
    while speed > 2.0:
        filters.append("atempo=2.0")
        speed /= 2.0
    while speed < 0.5:
        filters.append("atempo=0.5")
        speed /= 0.5
    filters.append(f"atempo={speed:.6f}")
    return ",".join(filters)

def main():
    if len(sys.argv) != 3:
        print(f"Usage: python {sys.argv[0]} <input_wav_path> <target_duration_seconds>")
        sys.exit(1)

    input_path = sys.argv[1]
    target_duration = float(sys.argv[2])

    if not os.path.isfile(input_path):
        print(f"Input file not found: {input_path}")
        sys.exit(1)

    # Get original duration
    original_duration = get_audio_duration(input_path)
    print(f"Original duration: {original_duration:.2f} seconds")

    if original_duration <= 0 or target_duration <= 0:
        print("Invalid durations.")
        sys.exit(1)

    speed = original_duration / target_duration
    print(f"Speed factor: {speed:.4f}")

    # Build output filename
    base, ext = os.path.splitext(input_path)
    ab = str(int(target_duration)).zfill(2)
    cd = str(int(round((target_duration - int(target_duration)) * 100))).zfill(2)
    output_path = f"{base}_output_{ab}_{cd}{ext}"

    # Build ffmpeg atempo filter string
    atempo_filter = build_atempo_filters(speed)
    print(f"Applying ffmpeg filter: {atempo_filter}")

    ffmpeg_cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-filter:a", atempo_filter,
        output_path
    ]
    try:
        subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print("ffmpeg failed:", e.stderr.decode())
        sys.exit(1)

    # Check output duration
    output_duration = get_audio_duration(output_path)
    print(f"Output file: {output_path}")
    print(f"Output duration: {output_duration:.2f} seconds")
    print(f"Target duration: {target_duration:.2f} seconds")
    print(f"Difference: {abs(output_duration - target_duration):.2f} seconds")

if __name__ == "__main__":
    main()
