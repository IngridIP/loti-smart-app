import streamlit as st
import geopandas as gpd
import folium
from shapely.geometry import Polygon
from streamlit_folium import st_folium
import io
import pandas as pd
from datetime import datetime

# Configuración de la app
st.set_page_config(page_title="IA Lotizadora", layout="wide")
st.title("🏗️ LotiSmart - IA para Lotización Automática")

# Sidebar para cargar el archivo y parámetros
st.sidebar.header("📂 Cargar plano")
archivo = st.sidebar.file_uploader("Sube un archivo SHP, GeoJSON o KML", type=["shp", "geojson", "kml", "zip"])

min_area = st.sidebar.number_input("Área mínima del lote (m²)", min_value=50, value=150)
generar = st.sidebar.button("Generar lotes")

# Leer y procesar el archivo
if archivo and generar:
    if archivo.name.endswith(".zip"):
        gdf = gpd.read_file(f"zip://{archivo.name}", vfs=f"zip://{archivo.name}")
    else:
        gdf = gpd.read_file(archivo)

    st.success("✅ Archivo cargado correctamente")
    st.write("### Vista previa del área")
    st.map(gdf)

    st.write("### Generando lotes...")

    union_geom = gdf.unary_union
    min_side = (min_area)**0.5
    bounds = union_geom.bounds
    x_min, y_min, x_max, y_max = bounds

    lotes = []
    x = x_min
    while x + min_side <= x_max:
        y = y_min
        while y + min_side <= y_max:
            lote = Polygon([
                (x, y),
                (x + min_side, y),
                (x + min_side, y + min_side),
                (x, y + min_side)
            ])
            if union_geom.contains(lote):
                lotes.append(lote)
            y += min_side
        x += min_side

    lotes_gdf = gpd.GeoDataFrame(geometry=lotes, crs=gdf.crs)

    st.success(f"✅ {len(lotes)} lotes generados")

    st.write("### Mapa interactivo")
    center = gdf.geometry.centroid.iloc[0].coords[:][0][::-1]
    m = folium.Map(location=center, zoom_start=17)
    folium.GeoJson(gdf, name="Área base").add_to(m)
    folium.GeoJson(lotes_gdf, name="Lotes", style_function=lambda x: {'color': 'green', 'fillOpacity': 0.3}).add_to(m)
    st_folium(m, width=900, height=500)

    st.write("### Descargar resultados")
    buffer = io.BytesIO()
    lotes_gdf.to_file(buffer, driver="GeoJSON")
    st.download_button("⬇️ Descargar GeoJSON de Lotes", buffer.getvalue(), file_name="lotes.geojson")

    # Guardar los datos en CSV
    session_data = {
        "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Archivo": archivo.name,
        "Área mínima (m²)": min_area,
        "Lotes generados": len(lotes),
    }

    try:
        # Intentar cargar el archivo CSV existente
        df = pd.read_csv("datos_lotizacion.csv")
    except FileNotFoundError:
        # Si no existe, crear uno nuevo
        df = pd.DataFrame(columns=["Fecha", "Archivo", "Área mínima (m²)", "Lotes generados"])

    # Agregar los nuevos datos
    df = df.append(session_data, ignore_index=True)

    # Guardar el CSV actualizado
    df.to_csv("datos_lotizacion.csv", index=False)

else:
    st.info("Sube un archivo y presiona 'Generar lotes' para empezar.")
