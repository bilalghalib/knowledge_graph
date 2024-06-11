import json
import re
import argparse
import pandas as pd
from pathlib import Path
import hashlib
import signal

class TimeoutExpired(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutExpired

# Set the signal handler for timeout
signal.signal(signal.SIGALRM, timeout_handler)

def extract_json_from_text(text):
    """
    Extract valid JSON objects from a given text.

    Parameters:
    text (str): The input text containing JSON objects and other random text.

    Returns:
    list: A list of valid JSON objects extracted from the text.
    """
    # Use regular expression to find potential JSON objects
    json_pattern = re.compile(r'\{.*?\}', re.DOTALL)
    json_objects = []
    
    matches = json_pattern.findall(text)
    for match in matches:
        try:
            json_obj = json.loads(match)
            # Generate a hash for the chunk_id
            chunk_id = hashlib.md5(match.encode()).hexdigest()
            json_obj["chunk_id"] = chunk_id
            json_objects.append(json_obj)
        except json.JSONDecodeError:
            continue  # Skip invalid JSON

    return json_objects

def extract_conceptual_space(text):
    """
    Extract conceptual neighborhoods from a given text block.

    Parameters:
    text (str): The input text containing conceptual neighborhoods.

    Returns:
    dict: A dictionary representing the conceptual space.
    """
    # Use regular expression to find all concepts within brackets
    concept_pattern = re.compile(r'\[.*?\]', re.DOTALL)
    matches = concept_pattern.findall(text)

    # Clean the matches and create the conceptual space dictionary
    conceptual_space = {"all concepts": []}
    for match in matches:
        # Remove brackets and split by commas
        concepts = match.strip('[]').split(', ')
        conceptual_space["all concepts"].append(concepts)

    return conceptual_space

def main(input_file, output_directory):
    # Read the input text file
    with open(input_file, 'r') as file:
        input_text = file.read()
    
    # Extract JSON objects from the input text
    json_objects = extract_json_from_text(input_text)
    
    # Extract conceptual space from the input text
    conceptual_space = extract_conceptual_space(input_text)
    
    # Combine the extracted JSON objects into a single JSON array
    final_json = json.dumps(json_objects, indent=4)
    
    # Save the final JSON to a file
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    
    json_output_file = output_directory / 'cleaned_data.json'
    with open(json_output_file, 'w') as f:
        f.write(final_json)
    
    print(f"Cleaned JSON data has been saved to {json_output_file}")

    # Save the JSON objects to a CSV file
    if json_objects:
        df = pd.DataFrame(json_objects)
        csv_output_file = output_directory / 'graph.csv'
        df.to_csv(csv_output_file, sep='|', index=False)
        print(f"CSV data has been saved to {csv_output_file}")
    else:
        print("No valid JSON objects found to save to CSV.")

    # Save the conceptual space to a JSON file
    conceptual_space_file = output_directory / 'conceptual_space.json'
    with open(conceptual_space_file, 'w') as f:
        json.dump(conceptual_space, f, indent=4)
    print(f"Conceptual space data has been saved to {conceptual_space_file}")

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Extract valid JSON objects and conceptual space from a text file.')
    parser.add_argument('input_file', type=str, help='The path to the input text file')
    parser.add_argument('output_directory', type=str, help='The directory where the output files will be saved')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Prompt for the output filename with a timeout of 10 seconds
    output_filename = 'clean_json'
    print("Please enter the output filename (default is 'clean_json'):")
    
    try:
        signal.alarm(10)
        output_filename = input()
        signal.alarm(0)
    except TimeoutExpired:
        print("\nTimeout reached, using default output filename 'clean_json'.")

    # Run the main function with the provided input file and output directory
    main(args.input_file, args.output_directory)
