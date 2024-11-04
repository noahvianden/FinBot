import os
import jsonlines

input_directory = "../historical_post_data_clean"

def process_files(input_dir, output_dir, threshold):
    # Dictionary zum Speichern der geöffneten Writer
    writers = {}

    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith(".jsonl"):
                file_path = os.path.join(root, file)
                process_file(file_path, input_dir, output_dir, writers, threshold)

    # Alle Writer schließen
    for writer in writers.values():
        writer.close()

def process_file(file_path, input_dir, output_dir, writers, threshold):
    with jsonlines.open(file_path) as reader:
        for post in reader:
            if post.get("num_comments", 0) > threshold:
                write_filtered_post(post, file_path, input_dir, output_dir, writers)

def write_filtered_post(post, original_file_path, input_dir, output_dir, writers):
    # Relativen Pfad vom Eingabeverzeichnis erhalten
    rel_path = os.path.relpath(original_file_path, input_dir)
    parts = rel_path.split(os.sep)

    # Annahme der Struktur: Jahr/Monat/Dateiname
    if len(parts) >= 3:
        year = parts[0]
        month = parts[1]
        filename = parts[2]
    else:
        # Unerwartete Dateistruktur behandeln
        print(f"Unerwartete Dateistruktur: {original_file_path}")
        return

    # Tag aus dem Dateinamen extrahieren
    day = filename.split("_")[-1].split(".")[0]

    # Ausgabepfad konstruieren
    output_year_dir = os.path.join(output_dir, year)
    output_month_dir = os.path.join(output_year_dir, month)
    os.makedirs(output_month_dir, exist_ok=True)
    output_file_name = f"reddit_{year}_{month}_{day}.jsonl"
    output_file_path = os.path.join(output_month_dir, output_file_name)

    # Writer aus dem Dictionary abrufen oder neuen erstellen
    if output_file_path not in writers:
        writers[output_file_path] = jsonlines.open(output_file_path, mode='a')

    # Gefilterten Post schreiben
    writers[output_file_path].write(post)

# Hauptprogramm: Schleife über die Schwellenwerte
for threshold in range(10, 101, 10):
    output_directory = f"output_filtered_{threshold}"
    # Sicherstellen, dass das Ausgabeverzeichnis existiert
    os.makedirs(output_directory, exist_ok=True)
    print(f"Verarbeite mit Schwellenwert {threshold}...")
    process_files(input_directory, output_directory, threshold)
