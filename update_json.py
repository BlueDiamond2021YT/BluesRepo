# Create downloads directory if it doesn't exist
os.makedirs('./downloads', exist_ok=True)

# Extract the .ipa file from the downloaded zip and save it in ./downloads/
with zipfile.ZipFile(io.BytesIO(zip_response.content)) as z:
    ipa_files = [f for f in z.namelist() if f.endswith('.ipa')]
    
    if not ipa_files:
        print("No .ipa files found in the artifact.")
        exit(1)
    
    # Assuming we take the first .ipa file found
    ipa_file_name = ipa_files[0]
    
    # Define version for naming and save path
    version = latest_run['head_commit']['id'][:7]  # Shorten commit hash for filename
    save_path = f"./downloads/{ipa_file_name[:-4]}-{version}.ipa"

    # Extract and save .ipa file to specified path
    with open(save_path, 'wb') as ipa_file:
        ipa_file.write(z.read(ipa_file_name))

print(f"Extracted and saved IPA File: {save_path}")
