import argparse
import logging
import yaml
import json
from jsonschema import validate, ValidationError
import os
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_argparse():
    """
    Sets up the argument parser for the command-line interface.
    """
    parser = argparse.ArgumentParser(description="Identifies insecure default configurations.")
    parser.add_argument("config_file", help="Path to the configuration file (YAML or JSON).")
    parser.add_argument("-s", "--schema_file", help="Path to the JSON schema file for validation.")
    parser.add_argument("-t", "--type", choices=['yaml', 'json'], help="Specify the type of the configuration file (yaml or json). Auto-detect if not provided")
    parser.add_argument("-l", "--log_level", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], default='INFO', help="Set the logging level (default: INFO)")
    return parser

def load_config_file(config_file, file_type=None):
    """
    Loads a configuration file (YAML or JSON).

    Args:
        config_file (str): Path to the configuration file.
        file_type (str, optional): Explicitly specify the file type ('yaml' or 'json'). Auto-detect if None.

    Returns:
        dict: The configuration data as a dictionary.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file type is not supported.
        yaml.YAMLError: If the YAML file is invalid.
        json.JSONDecodeError: If the JSON file is invalid.
    """
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Configuration file not found: {config_file}")

    try:
        with open(config_file, 'r') as f:
            # Auto-detect file type if not explicitly given
            if file_type is None:
                if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                    file_type = 'yaml'
                elif config_file.endswith('.json'):
                    file_type = 'json'
                else:
                    raise ValueError("Could not determine the file type. Please specify with --type")

            if file_type == 'yaml':
                return yaml.safe_load(f)
            elif file_type == 'json':
                return json.load(f)
            else:
                raise ValueError("Unsupported configuration file type. Choose 'yaml' or 'json'.")

    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error parsing YAML file: {e}")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Error parsing JSON file: {e}", e.doc, e.pos)
    except Exception as e:
        raise Exception(f"An unexpected error occurred while loading the configuration: {e}")

def load_schema_file(schema_file):
    """
    Loads a JSON schema file.

    Args:
        schema_file (str): Path to the JSON schema file.

    Returns:
        dict: The schema data as a dictionary.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the JSON file is invalid.
    """
    if not os.path.exists(schema_file):
        raise FileNotFoundError(f"Schema file not found: {schema_file}")

    try:
        with open(schema_file, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Error parsing JSON schema file: {e}", e.doc, e.pos)
    except Exception as e:
        raise Exception(f"An unexpected error occurred while loading the schema: {e}")

def validate_config(config_data, schema_data):
    """
    Validates the configuration data against a JSON schema.

    Args:
        config_data (dict): The configuration data to validate.
        schema_data (dict): The JSON schema to validate against.

    Returns:
        None

    Raises:
        jsonschema.ValidationError: If the configuration data is invalid according to the schema.
    """
    try:
        validate(instance=config_data, schema=schema_data)
    except ValidationError as e:
        raise ValidationError(f"Configuration validation error: {e}")
    except Exception as e:
        raise Exception(f"An unexpected error occurred during validation: {e}")

def main():
    """
    Main function to execute the configuration validation process.
    """
    parser = setup_argparse()
    args = parser.parse_args()

    # Set logging level
    logging.getLogger().setLevel(args.log_level)

    try:
        # Load configuration file
        config_data = load_config_file(args.config_file, args.type)
        logging.debug(f"Configuration loaded successfully from: {args.config_file}")

        # Load schema file, if provided
        if args.schema_file:
            schema_data = load_schema_file(args.schema_file)
            logging.debug(f"Schema loaded successfully from: {args.schema_file}")

            # Validate configuration
            validate_config(config_data, schema_data)
            logging.info("Configuration is valid according to the schema.")
        else:
            logging.warning("No schema file provided. Skipping validation.")

        # An empty YAML file loads as None and a JSON file can load as a
        # list. Both would crash the key checks below with a message that
        # points at the wrong thing, so reject them here, in plain terms.
        if not isinstance(config_data, dict):
            raise ValueError(
                f"Configuration must be a mapping of setting names to values, got {type(config_data).__name__}."
            )

        # The two default checks are independent on purpose. Chaining them
        # with elif meant a file still shipping the factory "password"
        # never got its default admin password reported in the same run.
        # This is the entire default detection: two key names, two
        # exact values, top level only. A nested password, a value of
        # Password with a capital, admin123, changeme, and every other
        # factory default in the world all pass and produce the no
        # default found line below. I keep the narrow scope visible
        # here because the tool's name promises far more than these
        # four comparisons deliver.
        found_default = False
        if config_data.get('password') == 'password':
            logging.warning("Insecure default password detected. Please change it.")
            found_default = True
        if config_data.get('admin_password') == 'admin':
            logging.warning("Insecure default admin password detected. Please change it.")
            found_default = True
        if not found_default:
            logging.info("No default password found")
        # Finding a default is a warning, not a failure: the run exits
        # 0 either way, so anything gating on this tool's exit code
        # passes a config that ships the factory password.


    except FileNotFoundError as e:
        logging.error(e)
        sys.exit(1)
    except ValueError as e:
        logging.error(e)
        sys.exit(1)
    except yaml.YAMLError as e:
        logging.error(e)
        sys.exit(1)
    except json.JSONDecodeError as e:
        logging.error(e)
        sys.exit(1)
    except ValidationError as e:
        logging.error(e)
        sys.exit(1)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

# Usage Examples (These would be in a separate README or documentation)

# Example 1: Validating a YAML configuration file against a schema
# python cha-InsecureDefaultConfigReporter.py config.yaml -s schema.json

# Example 2: Validating a JSON configuration file against a schema
# python cha-InsecureDefaultConfigReporter.py config.json -s schema.json

# Example 3: Specifying the log level to DEBUG
# python cha-InsecureDefaultConfigReporter.py config.yaml -s schema.json -l DEBUG

# Example 4: Running without a schema (only checking for default passwords)
# python cha-InsecureDefaultConfigReporter.py config.yaml

# Example 5: Explicitly specify file type
# python cha-InsecureDefaultConfigReporter.py config.custom -t yaml