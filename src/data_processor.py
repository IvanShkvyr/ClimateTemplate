from pathlib import Path

from matplotlib.colors import BoundaryNorm, ListedColormap, Normalize
import matplotlib.pyplot as plt
import numpy as np
from pyproj import CRS
import rasterio
from rasterio.plot import show
from rasterio.warp import reproject, Resampling, calculate_default_transform

from src.constants import CRS_FOR_DATA, PALETTES
from src.data_loader import read_and_clip_raster
from src.data_visualizer import combine_maps_with_layout



def convert_coordinate_systen_in_raster(crs_mercator:CRS ,output_path: str, output_path_2: str) -> None:
    """TODO"""
    # Відкриваємо перетворений растр
    with rasterio.open(output_path) as src:
        print(f"Координатна система растра {src.crs}")

        if src.crs != crs_mercator:
            # Обчислюємо нову трансформацію для CRS Web Mercator
            transform, width, height = calculate_default_transform(
                src.crs, crs_mercator, src.width, src.height, *src.bounds
            )

            # Отримуємо значення NoData з оригінального растра
            nodata_value = src.nodata

            # Відкриваємо новий файл для запису перетворених даних
            with rasterio.open(output_path_2, "w", driver="GTiff",
                            count=1, dtype=src.dtypes[0],
                            crs=crs_mercator, transform=transform,
                            width=width, height=height, nodata=nodata_value) as dst:
                
                # Перетворюємо дані з оригінальної системи координат в Web Mercator
                reproject(
                    source=rasterio.band(src, 1),
                    destination=rasterio.band(dst, 1),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=crs_mercator,
                    resampling=Resampling.nearest
                )

            print(f"Растер перетворений та збережений у {output_path_2}")
            
        else:
            print("Растер вже у Web Mercator.")


def create_visualization_with_shapefiles(raster_file, final_path, colors_list, classes, shapefile_1, shapefile_2, shapefile_3):

    # Завантажуємо растр
    with rasterio.open(raster_file) as src:
        raster_data = src.read(1)  # читаємо перший канал
        transform = src.transform  # географічна прив'язка
        crs = src.crs  # система координат
        nodata_value = src.nodata  # значення NoData, якщо є


    # Отримуємо унікальні значення (класи) в растрі
    unique_classes = np.unique(raster_data)

    # Фільтруємо палітру та boundaries тільки для унікальних класів
    filtered_boundaries = [b for b in classes if b in unique_classes]
    filtered_colors = [colors_list[i] for i in range(len(classes)) if classes[i] in unique_classes]



    if len(filtered_boundaries) > 1:
        # Створюємо палітру
        cmap = ListedColormap([tuple(c / 255.0 for c in color) for color in filtered_colors])

        # Створюємо нормалізацію за унікальними класами
        norm = BoundaryNorm(filtered_boundaries, cmap.N, extend='max')

    else:
        # Якщо є лише один унікальний клас
        cmap = ListedColormap([tuple(c / 255.0 for c in filtered_colors[0])])  # Один колір

        # Створюємо просту нормалізацію для одного класу
        norm = Normalize(vmin=filtered_boundaries[0] - 0.5, vmax=filtered_boundaries[0] + 0.5)

    normalized_values = norm(raster_data)

    # Створюємо фігуру для відображення
    fig, ax = plt.subplots(figsize=(21, 21), dpi=300)

    # Налаштовуємо розмір виводу
    ax.set_xlim([transform[2], transform[2] + src.width * transform[0]])
    ax.set_ylim([transform[5] + src.height * transform[4], transform[5]])

    # Маскуємо значення NoData та -999
    raster_data = np.ma.masked_where(raster_data == -999, raster_data)

    if nodata_value is not None:
        raster_data = np.ma.masked_equal(raster_data, nodata_value)

    # Відображаємо растр з палітрою
    show(normalized_values, ax=ax, cmap=cmap, transform=transform)

    # Накладаємо шейпфайл 3
    shapefile_3.plot(ax=ax, facecolor=(156/255, 156/255, 156/255), edgecolor='none', linewidth=3)

    # Накладаємо шейпфайл 1
    shapefile_1.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=1.2)

    # Накладаємо шейпфайл 2
    shapefile_2.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=3.2)


    # Видаляємо осі
    ax.set_axis_off()

    # Збереження фінального зображення
    plt.savefig(final_path, format='png', dpi=300, bbox_inches='tight', pad_inches=-0.03)

    plt.close(fig)


def ensure_directory_exists(directory_path: str) -> Path:
    """
    Ensure that the specified exists. If not? create it.
    
    Parameters:
        directory_path (str or Path): The path to the folder to check or create.
        
    Returns:
        Path: The Path object of the ensured directory.
    """
    path = Path(directory_path)

    # Ensure that the directory exists, if not create it
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

    return path


def ensure_directories_exist(folders):
    """Перевіряє існування директорій та створює їх, якщо потрібно."""
    return {folder: ensure_directory_exists(folder) for folder in folders}


def process_rasters(list_of_rasters, mask_shape, tump_folder, tump_folder_img):
    """Обробка растрів, вирізка та зміна системи координат."""
    list_of_img = []
    for raster in list_of_rasters:
        output_path = tump_folder / raster.name
        output_path_2 = tump_folder_img / raster.name
        read_and_clip_raster(raster, mask_shape, output_path)
        convert_coordinate_systen_in_raster(CRS_FOR_DATA, output_path, output_path_2)
        list_of_img.append(output_path_2)
    return list_of_img


def process_raster_for_layout(raster_path,
            list_for_background_layout,
            countries_shapefile,
            central_countries_shapefile,
            sea_shapefile,
            work_folder):
                   
    # Отримуємо тип з імені файлу
        raster_parts_name = raster_path.stem.split("_")
        raster_type = raster_parts_name[
            0
        ]  # Беремо частину імені до першого підкреслення

        # Вибір палітри залежно від типу
        if raster_type not in PALETTES:
            raise ValueError(f"Палітра для типу {raster_type} не знайдена")

        # Завантажуємо палітру та межі для даного типу
        palettes = PALETTES[raster_type]
        boundaries = palettes["boundaries"]
        colors = palettes["colors"]
        classes = palettes["classes"]

        if raster_type not in ["AWP", "FWI"]:

            raster_path = reclassify_raster(raster_path, work_folder, boundaries)

        img_path = work_folder / raster_path.name

        print(img_path)

        create_visualization_with_shapefiles(
            raster_path,
            img_path,
            colors,
            classes,
            countries_shapefile,
            central_countries_shapefile,
            sea_shapefile,
        )

        if "AW" in raster_type:
            background_type = "_".join([raster_parts_name[0], raster_parts_name[1]])
            background_type = background_type[:-2]
        elif "FWI" in raster_type:
            background_type = "FWI_GenZ"
        else:
            background_type = raster_parts_name[0]

        if background_type not in list_for_background_layout:
            list_for_background_layout[background_type] = []

        print(f"background_type {background_type}")

        list_for_background_layout[background_type].append(img_path)


def process_backgrounds(list_of_background, list_for_background_layout, work_folder):
    """Обробка фону та комбінування карт."""
    for background in list_of_background:
        date_labels = []
        background_type = background.stem
        if "AW" in background_type:
            background_type = background_type[3:-2]
        else:
            background_type = background_type[3:]

        try:
            img_list = list_for_background_layout[background_type]
        except KeyError:
            print(f"Немає {background_type}")
            continue

        for img in img_list:
            date = img.stem.split("_")[-1]
            date_labels.append(date)

        out_comp_file = work_folder / f"{background_type}.png"
        combine_maps_with_layout(background, img_list, date_labels, out_comp_file)


def reclassify_raster(raster_path, output_raster_path, boundaries):

    # Завантаження растру
    with rasterio.open(raster_path) as src:
        raster_data = src.read(1)  # Читаємо перший канал
        profile = src.profile
        nodata_value = src.nodata if src.nodata is not None else -999.0
    
    classes = np.digitize(raster_data, bins=boundaries, right=True) - 1  # Перекласифікація
    
    # # Збереження NoData значень
    # classes[classes == -999] = nodata_value  # Замінюємо -999 на офіційне NoData  # Повертаємо NoData у вихідний файл
    

    final_path = output_raster_path / raster_path.name

    # Запис нового растру
    profile.update(dtype=rasterio.int16, count=1, nodata=nodata_value)  # Використовуємо int16 для NoData



    with rasterio.open(final_path, 'w', **profile) as dst:
        dst.write(classes.astype(rasterio.int16), 1)

    return final_path


