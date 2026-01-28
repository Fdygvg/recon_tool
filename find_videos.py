import os
import json
import time
from datetime import datetime

# ===== CONFIGURATION =====
DRIVE_TO_SEARCH = "E:\\"  # Search entire E: drive
OUTPUT_FILE = r"C:\Users\USER\Desktop\ALL_VIDEOS_FOUND.json"
VIDEO_EXTENSIONS = {
    '.mp4', '.avi', '.mov', '.wmv', '.mkv', '.flv', 
    '.m4v', '.mpg', '.mpeg', '.3gp', '.webm'
}
EXCLUDE_FOLDERS = {
    'Windows', '$RECYCLE.BIN', 'System Volume Information',
    'Recovery', 'Boot', 'Temp', 'Temporary Internet Files'
}
# =========================

def format_size(bytes):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.2f} TB"

def should_skip_folder(folder_path):
    """Check if we should skip this folder"""
    folder_name = os.path.basename(folder_path).lower()
    
    # Skip system folders
    for exclude in EXCLUDE_FOLDERS:
        if exclude.lower() in folder_name:
            return True
    
    # Skip hidden/system folders
    try:
        if os.name == 'nt':  # Windows
            import ctypes
            FILE_ATTRIBUTE_HIDDEN = 0x2
            FILE_ATTRIBUTE_SYSTEM = 0x4
            attrs = ctypes.windll.kernel32.GetFileAttributesW(folder_path)
            if attrs != -1 and (attrs & (FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM)):
                return True
    except:
        pass
    
    return False

def find_all_videos():
    print("=" * 70)
    print("🔍 ULTIMATE VIDEO SEARCH - SCANNING ENTIRE DRIVE")
    print("=" * 70)
    print(f"Drive: {DRIVE_TO_SEARCH}")
    print(f"Output: {OUTPUT_FILE}")
    print("=" * 70)
    print()
    
    if not os.path.exists(DRIVE_TO_SEARCH):
        print(f"❌ ERROR: Drive not found: {DRIVE_TO_SEARCH}")
        return []
    
    all_videos = []
    folders_scanned = 0
    files_scanned = 0
    start_time = time.time()
    
    try:
        # Walk through EVERY folder
        for root, dirs, files in os.walk(DRIVE_TO_SEARCH, topdown=True):
            # Filter out folders to skip
            dirs[:] = [d for d in dirs if not should_skip_folder(os.path.join(root, d))]
            
            folders_scanned += 1
            
            # Show progress
            if folders_scanned % 100 == 0:
                elapsed = time.time() - start_time
                print(f"📂 Folders: {folders_scanned:,} | Files: {files_scanned:,} | "
                      f"Videos: {len(all_videos)} | Time: {elapsed:.1f}s", end='\r')
            
            for file in files:
                files_scanned += 1
                ext = os.path.splitext(file)[1].lower()
                
                if ext in VIDEO_EXTENSIONS:
                    try:
                        full_path = os.path.join(root, file)
                        file_size = os.path.getsize(full_path)
                        mod_time = datetime.fromtimestamp(os.path.getmtime(full_path))
                        
                        video_info = {
                            'name': file,
                            'path': full_path,
                            'folder': root,
                            'extension': ext,
                            'size_bytes': file_size,
                            'size_human': format_size(file_size),
                            'modified': mod_time.strftime('%Y-%m-%d %H:%M:%S'),
                            'folder_type': 'Videos' if 'video' in root.lower() else 
                                         'Downloads' if 'download' in root.lower() else
                                         'Desktop' if 'desktop' in root.lower() else
                                         'Documents' if 'document' in root.lower() else
                                         'Other'
                        }
                        
                        all_videos.append(video_info)
                        
                        # Show found files in real-time
                        print(f"🎬 FOUND: {file} ({format_size(file_size)}) in {root[:50]}...", end='\r')
                        
                    except Exception as e:
                        continue  # Skip files we can't access
    
    except KeyboardInterrupt:
        print("\n\n⏹️ Search stopped by user.")
    
    # Clear line
    print(' ' * 100, end='\r')
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print("\n" + "=" * 70)
    print("📊 SEARCH COMPLETE!")
    print("=" * 70)
    print(f"Total folders scanned: {folders_scanned:,}")
    print(f"Total files scanned: {files_scanned:,}")
    print(f"Total videos found: {len(all_videos)}")
    
    if all_videos:
        total_size = sum(v['size_bytes'] for v in all_videos)
        print(f"Total video size: {format_size(total_size)}")
        print(f"Search time: {total_time:.1f} seconds")
        print(f"Average: {folders_scanned/total_time:.1f} folders/second")
        
        # Group by folder type
        print("\n📁 VIDEOS BY LOCATION:")
        from collections import Counter
        locations = Counter(v['folder_type'] for v in all_videos)
        for loc, count in locations.most_common():
            print(f"  {loc}: {count} videos")
        
        # Save results
        all_videos.sort(key=lambda x: x['size_bytes'], reverse=True)
        
        # Save as JSON
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'search_info': {
                    'drive': DRIVE_TO_SEARCH,
                    'total_videos': len(all_videos),
                    'search_time_seconds': total_time,
                    'timestamp': datetime.now().isoformat()
                },
                'videos': all_videos
            }, f, indent=2, ensure_ascii=False)
        
        # Save as readable text
        txt_file = OUTPUT_FILE.replace('.json', '.txt')
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("COMPLETE VIDEO FILE LIST\n")
            f.write("=" * 80 + "\n\n")
            
            for i, video in enumerate(all_videos, 1):
                f.write(f"{i:4}. {video['name']}\n")
                f.write(f"     📁 Location: {video['folder_type']}\n")
                f.write(f"     📍 Path: {video['path']}\n")
                f.write(f"     📊 Size: {video['size_human']}\n")
                f.write(f"     🔤 Type: {video['extension']}\n")
                f.write(f"     📅 Modified: {video['modified']}\n")
                f.write("-" * 80 + "\n")
        
        print(f"\n💾 JSON data saved to: {OUTPUT_FILE}")
        print(f"📝 Readable list saved to: {txt_file}")
        
        # Show top 5 largest
        print("\n🏆 TOP 5 LARGEST VIDEOS:")
        for i, video in enumerate(all_videos[:5], 1):
            print(f"{i}. {video['name']} ({video['size_human']})")
            print(f"   📍 {video['path'][:80]}...")
            print()
    
    else:
        print("❌ No video files found anywhere on the drive!")
        print("\nPossible reasons:")
        print("1. Videos were deleted")
        print("2. Videos are in different formats (.dat, .vob, etc.)")
        print("3. Drive has severe corruption")
        print("4. Videos were never on this drive")
    
    return all_videos

if __name__ == "__main__":
    try:
        print("Starting deep scan of entire drive...")
        print("This may take 10-30 minutes depending on drive size.")
        print("Press Ctrl+C to stop at any time.\n")
        input("Press Enter to begin...")
        
        find_all_videos()
        
        print("\n✨ Done! Check your Desktop for the results files.")
        input("Press Enter to exit...")
        
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")