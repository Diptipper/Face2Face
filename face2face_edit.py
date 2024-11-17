from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import pandas as pd
import os


# This is for refreshing the metadata file
def list_files_in_folder(folder_path):
    try:
        # List all files in the given directory
        files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        return files
    except FileNotFoundError:
        print(f"The folder '{folder_path}' does not exist.")
        return []
    except PermissionError:
        print(f"Permission denied to access '{folder_path}'.")
        return []

def read_metadata(output_file):
    existing_data = []
    try:
        with open(output_file, 'r') as f:
            for i,line in enumerate(f):
                line = line.replace("\n","")
                if i>0 :
                    existing_data += [line.split("\t")]
        print("Appending the existing metadata file.")
    except:
        print("Creating a new metadata file.")
    return existing_data

def write_files_with_tags(folder_path, output_file):
    
    recorded_metadata = read_metadata(output_file)
    recorded_files = [ elem[0] for elem in recorded_metadata ]

    files = list_files_in_folder(folder_path)
    saved_files = []
    try:
        with open(output_file, 'w') as f:
            f.write("Image\tDirection\tExpression\n")
            newline = False
            for file in files:
                if ".txt" in file:
                    continue
                if file in recorded_files :
                    ifile = recorded_files.index(file)
                    tags = "\t".join(recorded_metadata[ifile][1:])
                    if newline :
                        f.write(f"\n{file}\t{tags}")
                    else:
                        f.write(f"{file}\t{tags}")
                else:
                    if newline :
                        f.write(f"\n{file}\tm\t ")
                    else:
                        f.write(f"{file}\tm\t ")
                    print("appending ",file)
                saved_files += [file]
                newline = True
        #print(f"File '{output_file}' has been written with filenames and placeholder tags.")
    except Exception as e:
        print(f"An error occurred while writing the file: {e}")

    with open("templates/imglist.js", 'w') as f:
        f.write("const imglist = [\n")
        for ifile,file in enumerate(saved_files):
            if ifile>0:
                f.write(", ")
            f.write(f"\"{file}\"\n")
        f.write("                ];\n")


# -------------------------------------------------------------------------



app = Flask(__name__)

# Load and save spreadsheet data
def load_spreadsheet(filename):

    folder_path = 'images'
    output_file = folder_path+'/metadata.txt'
    write_files_with_tags(folder_path, output_file)

    return pd.read_csv(filename, delimiter="\t")

def save_spreadsheet(data, filename):
    data.to_csv(filename, sep="\t", index=False)
    print(f"Data saved to {filename}")  # Debugging output

@app.route('/images/<filename>')
def images(filename):
    return send_from_directory(os.path.join(app.root_path, 'images'), filename)

@app.route("/", methods=["GET", "POST"])
def index():
    filename = "images/metadata.txt"
    global data

    if request.method == "POST":

        # Retrieve the dimensions of the table
        num_rows = int(request.form.get("num_rows", 0))
        num_cols = int(request.form.get("num_cols", 0))
        
        # Construct updated data
        updated_data = []
        for row in range(num_rows):
            updated_row = []
            for col in range(num_cols):
                # Retrieve each cell's value from the form
                cell_value = request.form.get(f"{row}-{col}", "")
                cell_value = " " if cell_value=="" else cell_value
                updated_row.append(cell_value)
            updated_data.append(updated_row)

        # Convert updated data into a DataFrame with the correct columns
        data = pd.DataFrame(updated_data, columns=data.columns)
        
        # Save the DataFrame back to the file
        save_spreadsheet(data, filename)

        # Redirect to refresh the page and see the changes
        return redirect(url_for("index"))

    # Load data for GET request
    data = load_spreadsheet(filename)
    return render_template("index.html", data=data)

if __name__ == "__main__":
    app.run(debug=True)
