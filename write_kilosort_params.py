def write_params(kilosort_settings, output_directory):
    try:
        filename = output_directory / "params.py"
        with open(filename, "w") as f:
            f.write("# params.py\n")
            f.write(
                "# Generated automatically based on spikeinterface_to_binary output\n"
            )
            f.write("# Adjust parameters as needed for Kilosort4 sorting\n\n")
            f.write("settings = {\n")
            for key, value in kilosort_settings.items():
                # Format values correctly for Python dictionary syntax
                if isinstance(value, str):
                    f.write(f"    '{key}': '{value}',\n")
                elif isinstance(value, float):
                    f.write(
                        f"    '{key}': {value:.1f},\n"
                    )  # Format floats for readability
                else:
                    f.write(f"    '{key}': {value},\n")
            f.write("}\n")
        print(f"Successfully generated params.py at: {filename}")
    except IOError as e:
        print(f"Error writing params.py: {e}")
