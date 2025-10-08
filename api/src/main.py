"""
Main pipeline for FloatChat Sprint 1 - BGE-M3 Embedding Pipeline

This module orchestrates the complete embedding pipeline including text processing,
embedding generation, and FAISS index creation.
"""

import os
from tqdm import tqdm
import time
from typing import List, Dict, Any
from src.utils.config import Config
from src.embeddings.bge_embedder import BGEM3Embedder
from src.embeddings.text_processor import TextProcessor
from src.embeddings.faiss_manager import FAISSManager


def main():
    """Main pipeline for creating embeddings and FAISS index."""
    print("=" * 60)
    print("=== FloatChat Sprint 1: BGE-M3 Embedding Pipeline ===")
    print("=" * 60)

    start_time = time.time()

    try:
        # Initialize components
        print("\n1. Initializing components...")
        embedder = BGEM3Embedder()
        processor = TextProcessor()
        faiss_manager = FAISSManager("oceanographic_data_v1")

        # Print model information
        model_info = embedder.get_model_info()
        print(f"\n2. Model Information:")
        for key, value in model_info.items():
            print(f"   {key}: {value}")

        # Print configuration summary
        Config.print_config_summary()

        # Check for existing text files
        text_data_path = Config.TEXT_DATA_PATH
        if not os.path.exists(text_data_path):
            print(f"\nText data directory not found: {text_data_path}")
            print("Creating sample data for demonstration...")

            # Create sample oceanographic data
            create_sample_data()

        # Step 1: Process text files
        print(f"\n3. Processing text files...")
        print(f"   Looking for files in: {text_data_path}")

        chunks, texts_to_embed = processor.process_all_files(text_data_path)

        if len(chunks) == 0:
            print("No text chunks found. Please check your text files.")
            print("You can place .txt files in the data/text_files/ directory")
            return

        print(f"   Created {len(chunks)} text chunks")

        # Step 2: Generate embeddings
        print(f"\n4. Generating embeddings with BGE-M3...")
        print(f"   Device: {Config.DEVICE}")
        print(f"   Number of texts: {len(texts_to_embed)}")

        embeddings = embedder.embed_batch(texts_to_embed, batch_size=Config.DEFAULT_BATCH_SIZE)

        if not embeddings:
            print("Error: No embeddings generated!")
            return

        print(f"   Generated {len(embeddings)} embeddings")

        # Step 3: Create FAISS index
        print(f"\n5. Creating FAISS index...")
        index_type = "FLAT" if len(embeddings) < 1000 else "IVF"
        print(f"   Using index type: {index_type}")

        faiss_manager.create_index(embeddings, index_type=index_type)

        # Step 4: Save index and metadata
        print(f"\n6. Saving index and metadata...")
        faiss_manager.save_index(chunks)

        # Step 5: Test the system
        print(f"\n7. Testing the system...")
        test_queries = [
            "ocean temperature salinity profile",
            "ARGO float measurements",
            "biogeochemical sensors data",
            "CTD cast ocean depth",
            "Indian Ocean current velocity"
        ]

        print("Testing similarity search with sample queries:")
        for i, query in enumerate(test_queries, 1):
            print(f"\n   Test {i}: '{query}'")
            query_embedding = embedder.embed_query(query)
            scores, results = faiss_manager.search(query_embedding, k=3)

            print("   Top 3 results:")
            for j, result in enumerate(results[:3], 1):
                similarity = result.get('similarity_score', 0)
                source_file = result.get('metadata', {}).get('source_file', 'Unknown')
                text_preview = result.get('text', '')[:100] + "..." if len(result.get('text', '')) > 100 else result.get('text', '')

                print(f"     {j}. Score: {similarity:.4f} | Source: {source_file}")
                print(f"        Text: {text_preview}")

        # Step 6: Test similarity calculation
        print(f"\n8. Testing similarity calculation...")
        test_texts = [
            ("Ocean temperature measurements from ARGO floats", "ARGO float temperature and salinity data"),
            ("Biogeochemical sensors in deep ocean", "Deep sea current measurements"),
            ("Surface water salinity profiles", "Mountain climbing equipment")
        ]

        print("   Pairwise similarity tests:")
        for text1, text2 in test_texts:
            similarity = embedder.calculate_similarity(text1, text2)
            print(f"     '{text1[:50]}...' vs '{text2[:50]}...': {similarity:.4f}")

        # Print final statistics
        stats = faiss_manager.get_stats()
        processing_stats = processor.get_processing_stats(chunks)

        print(f"\n9. Final Statistics:")
        print(f"\n9. Final Statistics:")
        print("   FAISS Index:")
        for key, value in stats.items():
            if key != 'config' and key != 'index_name':
                print(f"     {key}: {value}")

        print("   Text Processing:")
        for key, value in processing_stats.items():
            print(f"     {key}: {value}")

        # Calculate total time
        total_time = time.time() - start_time

        print("\n" + "=" * 60)
        print("=== BGE-M3 Embedding Pipeline Complete ===")
        print("=" * 60)
        print(f"Total execution time: {total_time:.2f} seconds")
        print(f"Index saved to: {faiss_manager.index_path}")
        print("Ready for RAG integration in Sprint 2!")
        print("\nNext steps:")
        print("1. Run 'python -m pytest tests/' to run tests")
        print("2. Use the search functionality in your applications")
        print("3. Integrate with LLM for RAG pipeline in Sprint 2")
    except Exception as e:
        print(f"\nError in main pipeline: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


def create_sample_data():
    """Create sample oceanographic data for testing."""
    print("Creating sample oceanographic data...")

    sample_data = {
        "argo_float_data.txt": """
        ARGO FLOAT MEASUREMENTS - INDIAN OCEAN

        Float ID: 5901234
        Location: 15.5°N, 75.2°E
        Date: 2023-06-15

        DEPTH PROFILE DATA:
        - Surface (0m): Temperature 28.5°C, Salinity 35.2 PSU, Pressure 0 dbar
        - 100m: Temperature 25.3°C, Salinity 35.8 PSU, Pressure 102 dbar
        - 500m: Temperature 12.8°C, Salinity 34.9 PSU, Pressure 512 dbar
        - 1000m: Temperature 8.2°C, Salinity 34.7 PSU, Pressure 1025 dbar
        - 1500m: Temperature 4.1°C, Salinity 34.8 PSU, Pressure 1538 dbar

        OXYGEN CONCENTRATIONS:
        - Mixed layer (0-50m): 4.8-5.2 ml/L
        - Thermocline (50-200m): 3.2-4.5 ml/L
        - Deep water (>1000m): 2.1-2.8 ml/L

        CURRENT MEASUREMENTS:
        - Surface currents: 0.3 m/s eastward
        - Mid-depth flows: 0.1 m/s westward at 800m
        - Deep circulation: <0.05 m/s
        """,

        "ctd_cast_report.txt": """
        CTD CAST REPORT - BAY OF BENGAL

        Cast Number: CTD-2023-045
        Position: 18°12'N, 89°45'E
        Date/Time: 2023-07-22 14:30 UTC
        Ship: R/V Sagar Kanya

        CAST PARAMETERS:
        Maximum Depth: 2500m
        Downcast Rate: 1.0 m/s
        Upcast Rate: 1.0 m/s
        Sensors: Temperature, Conductivity, Pressure, Oxygen, pH, Turbidity

        TEMPERATURE PROFILE:
        0-50m: 27.8-28.9°C (mixed layer)
        50-200m: 28.9-18.5°C (thermocline)
        200-1000m: 18.5-6.2°C (intermediate water)
        >1000m: 6.2-3.8°C (deep water)

        SALINITY STRUCTURE:
        0-50m: 32.5-33.8 PSU (low salinity surface)
        50-200m: 33.8-35.1 PSU (increasing with depth)
        200-1000m: 35.1-34.9 PSU (North Indian Deep Water)
        >1000m: 34.9-34.8 PSU (uniform deep salinity)

        BIOGEOCHEMICAL PARAMETERS:
        Chlorophyll-a maximum: 0.8 mg/m³ at 75m depth
        Oxygen minimum zone: 1.2 ml/L at 150m depth
        pH range: 8.2 (surface) to 7.8 (deep)
        Turbidity: 0.2-0.8 NTU (clear water conditions)
        """,

        "bgc_sensor_data.txt": """
        BIOGEOCHEMICAL SENSOR DATA - ARABIAN SEA

        Sensor Platform: BGC-Argo Float 6900987
        Mission: Oxygen and pH monitoring
        Location: 12.5°N, 68.8°E (Oman upwelling region)
        Date Range: 2023-05-01 to 2023-08-31

        SENSOR CALIBRATION:
        Oxygen Optode: Aanderaa 4831
        pH Sensor: Honeywell Durafet
        Accuracy: ±2 μmol/kg (oxygen), ±0.02 pH units

        SEASONAL VARIATIONS:

        MONSOON SEASON (June-August):
        - Surface oxygen: 180-220 μmol/kg
        - Deep oxygen minimum: 2-5 μmol/kg at 800m
        - pH surface: 8.15-8.25
        - pH deep: 7.75-7.85
        - Upwelling indicators: Low oxygen, high nutrients

        INTER-MONSOON PERIOD (March-May):
        - Surface oxygen: 200-240 μmol/kg
        - Deep oxygen: 5-15 μmol/kg
        - pH surface: 8.20-8.30
        - pH deep: 7.80-7.90
        - Stratified water column, oligotrophic conditions

        NITRATE CORRELATION:
        - Strong negative correlation with oxygen (r = -0.85)
        - Positive correlation with apparent oxygen utilization
        - Seasonal cycle driven by monsoon winds

        CARBON SYSTEM PARAMETERS:
        - Total alkalinity: 2350-2450 μmol/kg
        - DIC: 2100-2250 μmol/kg
        - Omega aragonite: 2.8-3.2 (surface supersaturation)
        """,

        "ocean_current_data.txt": """
        OCEAN CURRENT MEASUREMENTS - EQUATORIAL INDIAN OCEAN

        Measurement Platform: ADCP Moorings
        Location: Equatorial mooring array (0°N, 80°E)
        Period: 2022-2023 (annual cycle)
        Instrument: 75kHz RDI Workhorse ADCP

        ZONAL CURRENT (East-West):
        - Surface layer (0-100m): 0.8 m/s eastward (Wyrtki jets)
        - Thermocline (100-300m): 0.3 m/s westward (Equatorial Undercurrent)
        - Deep layer (>500m): <0.1 m/s variable direction

        MERIDIONAL CURRENT (North-South):
        - Surface divergence: ±0.2 m/s (seasonal)
        - Cross-equatorial flow: 0.1-0.3 m/s northward during monsoon
        - Deep circulation: <0.05 m/s

        SEASONAL CYCLE:
        - Northeast Monsoon (Dec-Feb): Strong eastward surface flow
        - Southwest Monsoon (Jun-Sep): Reversed circulation, upwelling
        - Transition periods: Weak, variable currents

        EDDY ACTIVITY:
        - Rossby wave propagation: 20-30 day period
        - Mesoscale eddies: 100-200 km diameter
        - Eddy kinetic energy: 100-500 cm²/s²

        TRANSPORT CALCULATIONS:
        - Indonesian Throughflow contribution: 0.2 m/s at 1000m
        - Somali Current influence: Seasonal signal at surface
        - Equatorial jet strength: Correlated with wind stress
        """,

        "satellite_sst_data.txt": """
        SATELLITE SEA SURFACE TEMPERATURE - INDIAN OCEAN

        Satellite: MODIS-Aqua (NASA)
        Resolution: 4km
        Period: 2023 (climatological year)
        Processing: Level 3, daily composites

        BASIN-SCALE PATTERNS:
        - Northern Indian Ocean: 28-32°C (warm pool)
        - Southern Indian Ocean: 18-25°C (subtropical gyre)
        - Equatorial region: 26-29°C (warm tongue)

        SEASONAL VARIABILITY:
        - Winter cooling: 2-3°C decrease in northern basin
        - Summer warming: 1-2°C increase in southern basin
        - Monsoon influence: 1°C cooling during southwest monsoon

        THERMAL FRONTS:
        - Agulhas Retroflection: 18-22°C gradient
        - Leeuwin Current: 22-26°C warm filament
        - Somali Current: Seasonal front formation

        SST ANOMALIES:
        - IOD positive phase: +1-2°C in eastern basin
        - IOD negative phase: -1-2°C cooling
        - ENSO correlation: +0.6 with eastern Pacific

        VALIDATION STATISTICS:
        - In-situ comparison: RMSE = 0.4°C
        - Bias correction: Applied for diurnal warming
        - Cloud masking: 85% valid pixels annually
        """
    }

    # Create data directory
    os.makedirs(Config.TEXT_DATA_PATH, exist_ok=True)

    # Write sample files
    for filename, content in sample_data.items():
        file_path = os.path.join(Config.TEXT_DATA_PATH, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content.strip())
        print(f"   Created: {filename}")

    print(f"Sample data created in: {Config.TEXT_DATA_PATH}")
    print("You can now run the pipeline or replace these with your own data.")


def search_interface():
    """Interactive search interface for testing the embedding system."""
    print("\n" + "=" * 50)
    print("FloatChat Search Interface")
    print("=" * 50)

    try:
        # Initialize components
        embedder = BGEM3Embedder()
        faiss_manager = FAISSManager("oceanographic_data_v1")

        # Load index
        if not faiss_manager.load_index():
            print("No existing index found. Please run the main pipeline first.")
            return

        print("Search interface ready!")
        print("Enter your oceanographic queries (type 'quit' to exit)")
        print("-" * 50)

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() in ['quit', 'exit', 'q']:
                    break

                if not query:
                    continue

                # Generate embedding
                query_embedding = embedder.embed_query(query)

                # Search
                scores, results = faiss_manager.search(query_embedding, k=5)

                # Display results
                print(f"\nTop {len(results)} results for: '{query}'")
                print("-" * 50)

                for i, result in enumerate(results, 1):
                    similarity = result.get('similarity_score', 0)
                    source_file = result.get('metadata', {}).get('source_file', 'Unknown')
                    text_content = result.get('text', '')

                    print(f"{i}. Similarity: {similarity:.4f}")
                    print(f"   Source: {source_file}")
                    print(f"   Text: {text_content[:200]}{'...' if len(text_content) > 200 else ''}")
                    print()

            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error during search: {e}")
                continue

    except Exception as e:
        print(f"Error initializing search interface: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "search":
        search_interface()
    else:
        main()
