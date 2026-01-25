import os

INPUT_DIR = "/Volumes/Extreme_SSD/MachineLearning/Log-Intelligence-System/data/processed/regex_candidates"  
OUTPUT_FILE = "/Volumes/Extreme_SSD/MachineLearning/Log-Intelligence-System/data/processed/regex_candidates/merged_clusters.txt"

def merge_files():
    # check if folder exists
    if not os.path.exists(INPUT_DIR):
        print(f"Error: Directory '{INPUT_DIR}' not found.")
        return

    # Open the output file in write mode
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:
        count = 0
        
        # Walk through directory and subdirectories
        for root, dirs, files in os.walk(INPUT_DIR):
            for file in files:
                if file.endswith(".txt"):
                    file_path = os.path.join(root, file)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as infile:
                            # Write a header to identify the source file
                            outfile.write(f"\n{'='*40}\n")
                            outfile.write(f"SOURCE: {file}\n")
                            outfile.write(f"{'='*40}\n")
                            
                            # Write the content
                            outfile.write(infile.read())
                            outfile.write("\n") # Ensure newline at end
                            
                            count += 1
                            print(f"Appended: {file}")
                            
                    except Exception as e:
                        print(f"Could not read {file}: {e}")

    print(f"\n[DONE] Successfully merged {count} files into '{OUTPUT_FILE}'")

if __name__ == "__main__":
    merge_files()