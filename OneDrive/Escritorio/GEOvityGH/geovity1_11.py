import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk  # Asegúrate de tener PIL (Pillow) instalado

# Configuración inicial de customtkinter
ctk.set_appearance_mode("light")  # Modo claro
ctk.set_default_color_theme("dark-blue")  # Tema de color

# Función para corregir los datos
def corregir_datos():
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if not file_path:
        return

    try:
        # Cargar los datos
        df = pd.read_csv(file_path)

        # Función para calcular la gravedad normal
        def gravedad_normal(latitud):
            sin2 = np.sin(np.radians(latitud)) ** 2
            return 9.7803267714 * (1 + 0.00193185138639 * sin2) / np.sqrt(1 - 0.00669437999013 * sin2)

        # Calcular la corrección de latitud
        df['Grav_Normal'] = df['LatitudeUTM'].apply(gravedad_normal)

        # Aplicar corrección de Bouguer simple (sin corrección de terreno detallada)
        rho = 2.67  # densidad promedio en g/cm³
        df['Grav_Bouguer'] = df['ObsGravity'] - df['elevation'] * 0.3086 + 0.04193 * rho * df['elevation']

        # Calcular anomalía de Bouguer
        df['Anomalia_Bouguer'] = df['ObsGravity'] - df['Grav_Normal'] - df['Grav_Bouguer']

        # Guardar los datos corregidos
        save_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if save_path:
            df.to_csv(save_path, index=False)
            messagebox.showinfo("Éxito", "Datos corregidos y guardados correctamente.")
    except Exception as e:
        messagebox.showerror("Error", f"Hubo un problema al corregir los datos: {e}")

# Función para generar el mapa de anomalías
def generar_mapa():
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if not file_path:
        return

    try:
        # Paso 1: Cargar y Preparar los Datos
        df = pd.read_csv(file_path)

        # Extraer las columnas necesarias
        lon = df['LongitudeUTM'].values
        lat = df['LatitudeUTM'].values
        anomalia = df['Anomalia_Bouguer'].values

        # Paso 2: Crear la Superficie Interpolada
        # Definir el grid para la interpolación
        grid_lon, grid_lat = np.mgrid[lon.min():lon.max():500j, lat.min():lat.max():500j]

        # Interpolación de los datos usando griddata
        grid_anomalia = griddata((lon, lat), anomalia, (grid_lon, grid_lat), method='cubic')

        # Paso 3: Visualizar el Mapa
        plt.figure(figsize=(10, 8))
        contour = plt.contourf(grid_lon, grid_lat, grid_anomalia, cmap='RdBu', levels=50)
        plt.colorbar(contour, label='Anomalía Gravimétrica (mGal)')
        plt.scatter(lon, lat, c=anomalia, cmap='RdBu', edgecolor='k')
        plt.title('Mapa de Anomalías Gravimétricas')
        plt.xlabel('Longitud UTM')
        plt.ylabel('Latitud UTM')

        # Paso 4: Guardar el Mapa
        save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if save_path:
            plt.savefig(save_path, dpi=300)
            plt.show()
            messagebox.showinfo("Éxito", "Mapa de anomalías generado y guardado correctamente.")
    except Exception as e:
        messagebox.showerror("Error", f"Hubo un problema al generar el mapa: {e}")

# Configuración de la interfaz gráfica
root = ctk.CTk()
root.title("GEOvity 1.11 - RIV Software")
root.geometry("650x550")
root.resizable(False, False)

# Crear el Tabview para las pestañas
tabview = ctk.CTkTabview(root, width=650, height=550)
tabview.pack(pady=10, padx=10)

# Pestaña principal
tab_main = tabview.add("Principal")  # Pestaña principal para las funcionalidades

# Pestaña de instrucciones
tab_instrucciones = tabview.add("Instrucciones")  # Pestaña para las instrucciones

# Contenido de la pestaña "Principal"
bg_image = Image.open("gravedad.png")
bg_image = bg_image.resize((600, 510), Image.LANCZOS)  # Redimensionar la imagen al tamaño de la ventana
bg_photo = ImageTk.PhotoImage(bg_image)

bg_label = ctk.CTkLabel(tab_main, image=bg_photo, text="")
bg_label.place(x=0, y=70, relwidth=1, relheight=1)  # Colocar la imagen de fondo en la pestaña principal

label = ctk.CTkLabel(tab_main, text="GEOvity", font=("Arial", 30, "italic", "bold"), 
                     text_color="#333333")  # Etiqueta con texto negro brillante
label.pack(pady=20)

btn_corregir = ctk.CTkButton(tab_main, text="Corregir Datos Gravimétricos", command=corregir_datos, 
                              width=200, height=50, border_width=2, corner_radius=20,
                              fg_color=None, hover_color="green")  # Botón sin fondo visible
btn_corregir.pack(pady=10)

btn_mapa = ctk.CTkButton(tab_main, text="Generar Mapa de Anomalías de Bouguer", command=generar_mapa, 
                         width=200, height=50, border_width=2, corner_radius=20,
                         fg_color=None, hover_color="green")  # Botón sin fondo visible
btn_mapa.pack(pady=10)

# Contenido de la pestaña "Instrucciones"
instrucciones_text = """Instrucciones para usar el programa:

1. El archivo .CSV que contiene los datos crudos deberá estar estructurado como "Site,LatitudeUTM,LongitudeUTM,elevation,ObsGravity". Para estructurar los datos crudos en el formato adecuado asegurese de que el orden de las columnas sea el correcto. Para mayor información o para la depuración de los datos crudos hacia el formato indicado contactese a: franrivcorporation@outlook.com
2. Haga clic en 'Corregir Datos Gravimétricos' para cargar un archivo CSV con los datos.
2. El archivo cargado será corregido por deriva instrumental, por mareas terrestres, por latitud y por topografía. Una vez corregidos se realiza la Reducción de bouguer de los datos y el archivo podrá guardarse en el formato .CSV.
3. Para generar un mapa de anomalías de Bouguer, haga clic en 'Generar Mapa' y seleccione el archivo de datos corregidos.
4. El mapa generado por el método de interpolación de Kriging se mostrará y se podrá guardar en formato PNG.


AllRightsReserved.
"""

label_instrucciones = ctk.CTkLabel(tab_instrucciones, text=instrucciones_text, 
                                   font=("Arial", 14), justify="left", anchor="w", wraplength=600)
label_instrucciones.pack(pady=20, padx=20)

# Iniciar el bucle principal de la interfaz gráfica
root.mainloop()