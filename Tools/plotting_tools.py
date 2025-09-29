import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature # Used for higher-quality map features
import numpy as np
import gsw  # Gibbs SeaWater Oceanographic Toolbox
import matplotlib.dates as mdates
from haversine import haversine, Unit
from sql_tools import engine as e

def save_and_return(fig, name):
    path = f"C:\\Users\\risha\\OneDrive\\Desktop\\SIH\\graphs\\plots\\{name}.png"
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return path

def plot_profile(profile_ids):
    # Normalize input (accept string or list)
    if isinstance(profile_ids, str):
        # handle "1900043,1900089" or "1900043, 1900089"
        profile_ids = [p.strip() for p in profile_ids.split(",") if p.strip()]
    elif not isinstance(profile_ids, list):
        # fallback: wrap single value in list
        profile_ids = [profile_ids]
    paths = []
    for profile_id in profile_ids:
        with e.connect() as conn:
            query = """
                SELECT pres AS depth, temp, psal
                FROM profile_levels
                WHERE profile_id = %s
                ORDER BY pres;
            """
            df = pd.read_sql(query, conn, params=(int(profile_id),))
            e.dispose()

            # --- Create figure and the first axis (for Temperature) ---
            fig, ax1 = plt.subplots(figsize=(6, 8), dpi=100)
            
            # --- Create the second axis that shares the y-axis ---
            ax2 = ax1.twiny()

            # Plot Temperature on the first axis (ax1)
            color1 = 'tab:blue'
            ax1.plot(df['temp'], df['depth'], color=color1, label='Temp (°C)')
            ax1.set_xlabel('Temperature (°C)', color=color1)
            ax1.tick_params(axis='x', labelcolor=color1)
            
            # Plot Salinity on the second axis (ax2)
            color2 = 'tab:orange'
            ax2.plot(df['psal'], df['depth'], color=color2, label='Salinity (PSU)')
            ax2.set_xlabel('Salinity (PSU)', color=color2)
            ax2.tick_params(axis='x', labelcolor=color2)
            
            # --- General Plot Formatting ---
            ax1.invert_yaxis() # Invert the primary y-axis
            ax1.set_ylabel("Depth (m)")
            ax1.set_title(f"Profile Plot (Profile {profile_id})")
            ax1.grid(True)
            
            # --- Create a single combined legend ---
            # To do this, we get the lines and labels from both axes
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax2.legend(lines1 + lines2, labels1 + labels2, loc='best')
            paths.append(save_and_return(fig, f"profile_{profile_id}"))
    return paths

def plot_ts_diagram(profile_ids):
    # Normalize input (accept string or list)
    if isinstance(profile_ids, str):
        # handle "1900043,1900089" or "1900043, 1900089"
        profile_ids = [p.strip() for p in profile_ids.split(",") if p.strip()]
    elif not isinstance(profile_ids, list):
        # fallback: wrap single value in list
        profile_ids = [profile_ids]
    paths = []
    for profile_id in profile_ids:
        with e.connect() as conn:

            query = """
                SELECT 
                    pl.temp AS temperature, 
                    pl.psal AS salinity, 
                    pl.pres AS depth, 
                    p.longitude AS lon, 
                    p.latitude AS lat
                FROM 
                    profile_levels AS pl
                JOIN 
                    profiles AS p ON pl.profile_id = p.id
                WHERE 
                    pl.profile_id = %s;
            """
            df = pd.read_sql(query, conn, params=(int(profile_id),))
            e.dispose()

            if df.empty:
                print(f"No data found for profile_id: {profile_id}")
                return

            # --- Step 2: Calculate Absolute Salinity and Conservative Temperature ---
            # GSW requires these for accurate density calculations.
            # We use the first lon/lat pair, assuming the profile is from one location.
            df['SA'] = gsw.SA_from_SP(df['salinity'], df['depth'], df['lon'][0], df['lat'][0])
            df['CT'] = gsw.CT_from_t(df['SA'], df['temperature'], df['depth'])

            fig, ax = plt.subplots(figsize=(8, 8), dpi=100)

            # --- Step 3: Create grid for plotting density contours (isopycnals) ---
            s_min, s_max = df['SA'].min(), df['SA'].max()
            t_min, t_max = df['CT'].min(), df['CT'].max()
            
            # Create grid
            s_grid = np.linspace(s_min, s_max, 100)
            t_grid = np.linspace(t_min, t_max, 100)
            S_grid, T_grid = np.meshgrid(s_grid, t_grid)
            
            # Calculate density on the grid
            density_grid = gsw.sigma0(S_grid, T_grid)
            
            # Plot the density contours
            contour = ax.contour(S_grid, T_grid, density_grid, colors='grey', linestyles='--', linewidths=0.7)
            ax.clabel(contour, inline=True, fontsize=8, fmt='%.1f') # Add labels to contours

            # --- Step 4: Plot the main data with improved aesthetics ---
            sc = ax.scatter(
                df['SA'], 
                df['CT'], 
                c=df['depth'], 
                cmap='viridis', 
                edgecolor='black', # Add edge to markers
                linewidth=0.5
            )
            
            # --- Step 5: Refine labels and add grid ---
            ax.set_xlabel("Absolute Salinity (g/kg)")
            ax.set_ylabel("Conservative Temperature (°C)")
            ax.set_title(f"T-S Diagram for Profile: {profile_id}") # Descriptive title
            ax.grid(True, linestyle=':', alpha=0.6) # Add a subtle grid
            
            cbar = fig.colorbar(sc, ax=ax, label="Depth (m)", pad=0.02)
            
            cbar.ax.invert_yaxis() 
            e.dispose()
            paths.append(save_and_return(fig, f"ts_diagram_{profile_id}"))
    return paths

def plot_trajectory(platform_numbers):
    # Normalize input (accept string or list)
    if isinstance(platform_numbers, str):
        # handle "1900043,1900089" or "1900043, 1900089"
        platform_numbers = [p.strip() for p in platform_numbers.split(",") if p.strip()]
    elif not isinstance(platform_numbers, list):
        # fallback: wrap single value in list
        platform_numbers = [platform_numbers]

    paths = []
    for platform_number in platform_numbers:
        with e.connect() as conn:
            query = """
                SELECT latitude, longitude, juld AS date
                FROM profiles
                WHERE platform_number = %s
                ORDER BY date;
            """
            df = pd.read_sql(query, conn, params=(platform_number,))

        if df.empty:
            print(f"No data found for platform_no: {platform_number}")
            continue

        # Convert juld to datetime
        df['datetime'] = pd.to_datetime(df['date'], unit='ns')

        # Use actual datetime for coloring
        color_variable = df['datetime']
        colorbar_label = "Time"

        fig = plt.figure(figsize=(8, 8), dpi=100)
        ax = plt.axes(projection=ccrs.PlateCarree())

        buffer = 5
        lat_min, lat_max = df['latitude'].min() - buffer, df['latitude'].max() + buffer
        lon_min, lon_max = df['longitude'].min() - buffer, df['longitude'].max() + buffer
        ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=ccrs.PlateCarree())

        # Add features
        ax.add_feature(cfeature.LAND, zorder=0, edgecolor='black')
        ax.add_feature(cfeature.OCEAN)
        ax.add_feature(cfeature.COASTLINE)
        ax.add_feature(cfeature.BORDERS, linestyle=':')

        gl = ax.gridlines(draw_labels=True, linewidth=1, color='gray', alpha=0.5, linestyle='--')
        gl.top_labels = False
        gl.right_labels = False

        # Scatter trajectory with time progression
        sc = ax.scatter(
            df['longitude'],
            df['latitude'],
            c=color_variable.astype("int64") // 10**9,  # convert datetime to seconds
            cmap='viridis',
            transform=ccrs.Geodetic()
        )

        cbar = fig.colorbar(sc, ax=ax, orientation='vertical', pad=0.05, shrink=0.7)
        cbar.set_label(colorbar_label)

        ax.set_title(f"Float {platform_number} Trajectory")

        paths.append(save_and_return(fig, f"trajectory_{platform_number}"))

    return paths

def plot_hovmoller(platform_no: str, variable: str = "temp"):
    with e.connect() as conn:
        query = f"""
            SELECT
                p.juld AS date,
                pl.pres AS depth,
                pl.{variable}
            FROM
                profiles AS p
            JOIN
                profile_levels AS pl ON p.id = pl.profile_id
            WHERE
                p.platform_number = %s
            ORDER BY
                date, depth;
        """
        df = pd.read_sql(query, conn, params=[platform_no])
        e.dispose()

        if df.empty:
            print(f"No data for platform {platform_no}")
            return

        # --- NEW: Grid the irregular data onto a regular grid ---

        # 1. Convert date and get unique profiles
        df['datetime'] = pd.to_datetime(df['date'], unit='ns')
        unique_dates = sorted(df['datetime'].unique())

        # 2. Define the new, regular depth grid (e.g., every 10m)
        standard_depths = np.arange(0, 1001, 10)

        # 3. Create an empty array to hold the gridded data
        gridded_data = np.full((len(standard_depths), len(unique_dates)), np.nan)

        # 4. Loop through each profile and interpolate it onto the standard grid
        for i, date in enumerate(unique_dates):
            profile = df[df['datetime'] == date]
            if len(profile) < 2:
                continue
            
            # Interpolate this profile's variable onto the standard depths
            interpolated_values = np.interp(
                standard_depths,
                profile['depth'],
                profile[variable]
            )
            gridded_data[:, i] = interpolated_values
        
        # --- The data is now a clean grid, ready for plotting ---

        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Use pcolormesh for plotting gridded data.
        # We use the gridded_data array, not the original DataFrame.
        mesh = ax.pcolormesh(unique_dates, standard_depths, gridded_data, cmap="coolwarm", shading='auto')
        fig.colorbar(mesh, ax=ax, label=f"{variable.capitalize()}")

        ax.invert_yaxis()
        ax.set_xlabel("Date")
        ax.set_ylabel("Depth (m)")
        ax.set_title(f"Hovmöller Diagram - {variable.capitalize()} (Float {platform_no})")
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        fig.autofmt_xdate()

        return save_and_return(fig, f"hovmoller_{variable}_{platform_no}")

# def plot_eulerian_hovmoller(lon_center: float, lon_width: float, start_date: str, end_date: str, variable: str = "temp"):
    
#     conn = get_connection()
    
#     # --- Step 1 & 2: Define Location and Query All Relevant Data ---
#     lon_min = lon_center - (lon_width / 2)
#     lon_max = lon_center + (lon_width / 2)

#     query = f"""
#         SELECT
#             p.juld AS date,
#             pl.pres AS depth,
#             pl.{variable} AS var
#         FROM
#             profiles AS p
#         JOIN
#             profile_levels AS pl ON p.id = pl.profile_id
#         WHERE
#             p.longitude BETWEEN %s AND %s
#             AND p.juld BETWEEN %s AND %s
#         ORDER BY
#             date, depth;
#     """
#     df = pd.read_sql(query, conn, params=(lon_min, lon_max, start_date, end_date))
#     conn.close()

#     if df.empty:
#         print(f"No data found in the specified location and date range.")
#         return

#     # --- Step 3: Grid and Interpolate the Data ---
#     df['datetime'] = pd.to_datetime(df['date'], unit='ns')
    
#     # Define the regular time grid (one point per month)
#     time_bins = pd.date_range(start=start_date, end=end_date, freq='MS') # MS for Month Start
    
#     # Define the regular depth grid
#     standard_depths = np.arange(0, 1001, 10)
    
#     # Create the empty grid to hold the final data
#     gridded_data = np.full((len(standard_depths), len(time_bins)), np.nan)

#     # Loop through each time bin (each month)
#     for i, month_start in enumerate(time_bins):
#         month_end = month_start + pd.offsets.MonthEnd(1)
        
#         # Select all data points that fall within this month
#         monthly_data = df[(df['datetime'] >= month_start) & (df['datetime'] <= month_end)]
        
#         if len(monthly_data) < 2:
#             continue
            
#         # Create a single "average profile" for the month by sorting all points by depth
#         # This effectively treats all data in the bin as one big profile
#         monthly_profile = monthly_data.sort_values('depth').drop_duplicates('depth')

#         if len(monthly_profile) < 2:
#             continue
            
#         # Interpolate this average monthly profile onto our standard depth grid
#         interpolated_values = np.interp(
#             standard_depths,
#             monthly_profile['depth'],
#             monthly_profile['var']
#         )
#         gridded_data[:, i] = interpolated_values

#     # --- Step 4: Plot the Final Grid ---
#     fig, ax = plt.subplots(figsize=(12, 6))
#     mesh = ax.pcolormesh(time_bins, standard_depths, gridded_data, cmap="coolwarm", shading='auto')
    
#     ax.invert_yaxis()
#     ax.set_ylabel("Depth (m)")
#     ax.set_xlabel("Date")
#     ax.set_title(f"Eulerian Hovmöller at {lon_center}°E (±{lon_width/2}°)")
#     fig.colorbar(mesh, ax=ax, label=f"{variable.capitalize()}")

#     ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
#     fig.autofmt_xdate()

#     return save_and_return(fig, f"hovmoller_eulerian_{variable}_{lon_center}E")

def plot_section(platform_number: str, start_date: str, end_date: str, variable: str = "temp"):
    with e.connect() as conn:
        loc_query = """
            SELECT id, latitude as lat, longitude as lon, juld
            FROM profiles
            WHERE platform_number = %s AND juld BETWEEN %s AND %s
            ORDER BY juld;
        """
        loc_df = pd.read_sql(loc_query, conn, params=(platform_number, start_date, end_date))

        if loc_df.empty:
            print(f"No profiles found for float {platform_number} in the specified date range.")
            e.dispose()
            return

        # Calculate cumulative distance along the track
        distances = [0]
        for i in range(1, len(loc_df)):
            prev_point = (loc_df['lat'].iloc[i-1], loc_df['lon'].iloc[i-1])
            curr_point = (loc_df['lat'].iloc[i], loc_df['lon'].iloc[i])
            dist_increment = haversine(prev_point, curr_point, unit=Unit.KILOMETERS)
            distances.append(distances[-1] + dist_increment)
        
        loc_df['distance'] = distances
        profile_ids = tuple(loc_df['id']) # Get a list of profile IDs for the next query

        # --- Step 3: Get Full Vertical Data and Merge ---
        data_query = f"""
            SELECT
                pl.profile_id,
                pl.pres AS depth,
                pl.{variable}
            FROM
                profile_levels AS pl
            WHERE
                pl.profile_id IN %s
            ORDER BY
                pl.profile_id, pl.pres;
        """
        df = pd.read_sql(data_query, conn, params=(profile_ids,))
        e.dispose()

        # Merge the calculated distance onto the main DataFrame
        df = pd.merge(df, loc_df[['id', 'distance']], left_on='profile_id', right_on='id')

        # --- Step 4: Grid the Data via Interpolation ---
        unique_distances = sorted(df['distance'].unique())
        standard_depths = np.arange(0, 1001, 10) # Grid every 10 meters
        gridded_data = np.full((len(standard_depths), len(unique_distances)), np.nan)

        for i, dist in enumerate(unique_distances):
            profile = df[df['distance'] == dist]
            if len(profile) < 2:
                continue
            
            interpolated_values = np.interp(
                standard_depths,
                profile['depth'],
                profile[variable]
            )
            gridded_data[:, i] = interpolated_values
            
        # --- Step 5: Visualize the Plot ---
        fig, ax = plt.subplots(figsize=(12, 6))
        mesh = ax.pcolormesh(unique_distances, standard_depths, gridded_data, cmap="coolwarm", shading='auto')
        fig.colorbar(mesh, ax=ax, label=f"{variable.capitalize()}")
        
        ax.invert_yaxis()
        ax.set_xlabel("Distance Along Track (km)")
        ax.set_ylabel("Depth (m)")
        ax.set_title(f"{variable.capitalize()} Section for Float {platform_number}")

        return save_and_return(fig, f"section_{variable}_{platform_number}")

def plot_3d_float_data(platform_number: str, variable: str = "temp"):
    with e.connect as conn:
        query = f"""
            SELECT
                p.longitude,
                p.latitude,
                pl.pres AS depth,
                pl.{variable}
            FROM
                profiles AS p
            JOIN
                profile_levels AS pl ON p.id = pl.profile_id
            WHERE
                p.platform_number = %s;
        """
        df = pd.read_sql(query, conn, params=(platform_number,))
        e.dispose()

        if df.empty:
            print(f"No data for platform {platform_number}")
            return

        # --- Create the 3D Plot ---
        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(projection='3d')

        # Create the 3D scatter plot
        # X-axis is Longitude, Y-axis is Latitude, Z-axis is Depth
        # Color represents the variable (e.g., Temperature)
        sc = ax.scatter(
            df['longitude'],
            df['latitude'],
            df['depth'],
            c=df[variable], # Use the variable for color
            cmap='coolwarm',
            s=5 # Make points smaller for clarity
        )

        # --- Formatting the plot ---
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.set_zlabel("Depth (m)")
        
        # Invert the Z-axis (depth) so 0 is at the top
        ax.invert_zaxis()
        
        ax.set_title(f"3D Data for Float {platform_number}")
        fig.colorbar(sc, ax=ax, shrink=0.6, label=f"{variable.capitalize()}")

        return save_and_return(fig, f"3d_{variable}_{platform_number}")

def plot_qc_comparison(profile_id: str, variable: str = "temp"):
    # Define variable names for the query
    raw_var = variable
    adj_var = f"{variable}_adjusted"
    qc_flag_var = f"{variable}_qc"

    query = f"""
        SELECT
            pres AS depth,
            {raw_var},
            {adj_var},
            {qc_flag_var}
        FROM
            profile_levels
        WHERE
            profile_id = %s
        ORDER BY
            pres;
    """
    with e.connect() as conn:
        df = pd.read_sql(query, conn, params=[int(profile_id)])
        e.dispose()

    if df.empty or df[adj_var].isnull().all():
        print(f"No data or no adjusted data for profile {profile_id}")
        return

    # --- Create a figure with two subplots ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 8), dpi=100)
    fig.suptitle(f"Quality Control Analysis for Profile {profile_id}", fontsize=16)

    # --- Panel 1: Raw vs. Adjusted Scatter Plot ---
    ax1.scatter(df[raw_var], df[adj_var], alpha=0.7)
    # Add a 1:1 reference line
    lims = [
        min(ax1.get_xlim()[0], ax1.get_ylim()[0]),
        max(ax1.get_xlim()[1], ax1.get_ylim()[1]),
    ]
    ax1.plot(lims, lims, 'r--', alpha=0.75, zorder=0, label='1:1 Line')
    ax1.set_xlabel(f"Raw {variable.capitalize()}")
    ax1.set_ylabel(f"Adjusted {variable.capitalize()}")
    ax1.set_title("Raw vs. Adjusted Values")
    ax1.grid(True, linestyle='--', alpha=0.5)
    ax1.legend()
    ax1.set_aspect('equal', 'box')


    # --- Panel 2: Profile Colored by QC Flag ---
    # QC flags are often stored as strings or numbers. Let's handle them as categories.
    df[qc_flag_var] = df[qc_flag_var].astype('category')
    scatter = ax2.scatter(df[adj_var], df['depth'], c=df[qc_flag_var].cat.codes,
                          cmap='viridis', vmin=0, vmax=8)
    ax2.invert_yaxis()
    ax2.set_xlabel(f"Adjusted {variable.capitalize()}")
    ax2.set_ylabel("Depth (m)")
    ax2.set_title("Profile Colored by QC Flag")
    ax2.grid(True, linestyle='--', alpha=0.5)
    
    # Create a legend for the QC flags
    # Standard Argo flags: 1=good, 2=probably good, 3=probably bad, 4=bad, etc.
    legend_handles = scatter.legend_elements()
    legend_labels = df[qc_flag_var].cat.categories
    ax2.legend(legend_handles[0], legend_labels, title="QC Flags")

    fig.tight_layout(rect=[0, 0, 1, 0.96]) # Adjust for suptitle

    return save_and_return(fig, f"qc_comparison_{variable}_{profile_id}")

def plot_depth_averaged_evolution(platform_no: str, variable: str = "temp", max_depth: str = "1000"):
    with e.connect as conn:
    # This single SQL query performs the entire averaging process efficiently.
        query = f"""
            SELECT
                p.juld AS date,
                AVG(pl.{variable}) as avg_variable
            FROM
                profiles AS p
            JOIN
                profile_levels AS pl ON p.id = pl.profile_id
            WHERE
                p.platform_number = %s
                AND pl.pres <= %s
            GROUP BY
                p.id, p.juld
            ORDER BY
                p.juld;
        """
        df = pd.read_sql(query, conn, params=[platform_no, int(max_depth)])

        if df.empty:
            print(f"Could not compute depth-averaged data for float {platform_no}")
            return

        # Convert Julian Day to a plottable datetime object
        df['datetime'] = pd.to_datetime(df['date'], unit='ns')

        # --- Plotting ---
        fig, ax = plt.subplots(figsize=(12, 6), dpi=100)

        ax.plot(df['datetime'], df['avg_variable'], marker='.', linestyle='-')

        # --- Formatting ---
        ax.set_xlabel("Date")
        ax.set_ylabel(f"Average {variable.capitalize()} (0-{max_depth}m)")
        ax.set_title(f"Depth-Averaged {variable.capitalize()} for Float {platform_no}")
        ax.grid(True, linestyle='--', alpha=0.6)

        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        fig.autofmt_xdate()
        e.dispose()
        return save_and_return(fig, f"depthaveraged_{variable}_{platform_no}")

def plot_time_series(platform_no: str, variable: str = "temp"):
    with e.connect() as conn:
    # Query for the surface measurement (level=0) and the date for each profile.
        query = f"""
            SELECT
                p.juld AS date,
                pl.{variable}
            FROM
                profiles AS p
            JOIN
                profile_levels AS pl ON p.id = pl.profile_id
            WHERE
                p.platform_number = %s
                AND pl.level = 0
            ORDER BY
                p.juld;
        """
        df = pd.read_sql(query, conn, params=[platform_no])

        if df.empty:
            print(f"No surface data found for float {platform_no}")
            return

        # Convert Julian Day (stored as nanoseconds) to a plottable datetime object
        df['datetime'] = pd.to_datetime(df['date'], unit='ns')

        # --- Plotting ---
        fig, ax = plt.subplots(figsize=(12, 6), dpi=100)

        ax.plot(df['datetime'], df[variable], marker='.', linestyle='-', markersize=4)

        # --- Formatting ---
        ax.set_xlabel("Date")
        ax.set_ylabel(f"Surface {variable.capitalize()}")
        ax.set_title(f"Surface {variable.capitalize()} Time Series for Float {platform_no}")
        ax.grid(True, linestyle='--', alpha=0.6)

        # Improve date formatting on the x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        fig.autofmt_xdate() # Rotates and aligns dates nicely

        e.dispose()
        return save_and_return(fig, f"timeseries_{variable}_{platform_no}")
    
