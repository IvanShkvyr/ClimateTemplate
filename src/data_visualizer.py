from PIL import Image, ImageDraw, ImageFont

from src.data_loader import load_config


path_config = load_config("config.yaml")

font_path = path_config["font_path"]


def combine_maps_with_layout(background_path, maps_list, labels_list, output_path):

    # Load the background layout
    background = Image.open(background_path).convert("RGBA")

    # Specify positioning and dimensions for maps and labels
    start_x = 24
    start_y = 94
    map_width = 850
    map_height = 906
    step_x = map_width + 18  # Horizontal step between maps
    step_y = map_height + 122  # Vertical step

    # Create a drawing object for adding labels
    draw = ImageDraw.Draw(background)
    font = ImageFont.truetype(font_path, size=62)

    # Place maps on the layout
    for idx, (map_path, label) in enumerate(zip(maps_list, labels_list)):
        # Calculate position
        row = idx // 5  # Create a new row every 5 maps
        col = idx % 5   # Place maps in a horizontal line (max 5 in a row)

        x = start_x + col * step_x
        y = start_y + row * step_y

        # Open map image
        map_image = Image.open(map_path).convert("RGBA")
        map_image = map_image.resize((map_width, map_height))

        # Paste the map on the background
        background.paste(map_image, (x, y))

        # Add label below the map
        label_x = x + 42
        label_y = y - 79
        draw.text((label_x, label_y), label, fill="black", font=font)

    # Save the final image
    background.save(output_path, "PNG", optimize=True, dpi=(300, 300))
    print("Layout saved to {}".format(output_path))