import os
import json
import geopandas as gpd
import pandas as pd

world = gpd.read_file("data/shapes/ne_110m_admin_0_countries.shp")
europe = world[world["CONTINENT"] == "Europe"]
gdf = gpd.read_file("data/IGGIELGN_PipeSegments.geojson")
gdf["param"] = gdf["param"].apply(json.loads)
gdf = gdf.join(gdf["param"].apply(pd.Series))

pipes_in_europe = gpd.sjoin(gdf, europe, how='inner', predicate='intersects')
pipes_in_europe = pipes_in_europe.rename(columns={"max_cap_M_m3_per_d": "Capacity in Million m^3/day", "NAME":"Country"})
pipes_in_europe = pipes_in_europe[["name", "Country", "geometry", "diameter_mm", "Capacity in Million m^3/day"]]
pipes_in_europe["Capacity in Million m^3/day"] = pipes_in_europe["Capacity in Million m^3/day"].round(3)

os.makedirs("maps", exist_ok=True)

countries = pipes_in_europe["Country"].unique()
countries.sort()

for country in countries:
    bounds = pipes_in_europe[pipes_in_europe["Country"] == country].total_bounds
    lat = (bounds[1] + bounds[3]) / 2
    lon = (bounds[0] + bounds[2]) / 2
    m = pipes_in_europe[pipes_in_europe["Country"] == country].explore(
    column="Capacity in Million m^3/day",    
    cmap="viridis",        
    legend=True,          
    tooltip=["diameter_mm", "Capacity in Million m^3/day"],   
    style_kwds={"weight": 3}, 
    tiles="CartoDB positron",
    location=[lat, lon],
    zoom_start=6,
    )
    m.save(f"maps/pipes_map_{country}.html")

header = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Pipeline Maps</title>
<style>
body { font-family: Arial, sans-serif; margin:0; padding:0; }
.tab { overflow: hidden; border-bottom: 1px solid #ccc; background-color: #f1f1f1; }
.tab button { background-color: inherit; float: left; border: none; outline: none; cursor: pointer; padding: 10px 16px; transition: 0.3s; }
.tab button:hover { background-color: #ddd; }
.tab button.active { background-color: #ccc; }
.tabcontent { display: none; width: 100%; height: 90vh; border: none; }
</style>
</head>
<body>

<h2>Pipeline Maps by Country</h2>

<div class="tab">

"""

footer = """

<script>
function openTab(evt, regionName, iframeSrc) {
  var i, tabcontent, tablinks;
  tabcontent = document.getElementsByClassName("tabcontent");
  for (i = 0; i < tabcontent.length; i++) { tabcontent[i].style.display = "none"; }
  tablinks = document.getElementsByClassName("tablinks");
  for (i = 0; i < tablinks.length; i++) { tablinks[i].className = tablinks[i].className.replace(" active", ""); }
  
  var tabDiv = document.getElementById(regionName);
  tabDiv.style.display = "block";
  evt.currentTarget.className += " active";
  
  // Lazy load iframe if it hasn't been loaded yet
  var iframe = tabDiv.querySelector("iframe");
  if (!iframe.src) {
      iframe.src = iframeSrc;
  }
}

document.getElementsByClassName('tablinks')[0].click();
</script>

</body>
</html>

"""

body1 = ""
body2 = ""
for country in countries:
    body1 += f"""<button class="tablinks" onclick="openTab(event,'{country}')">{country}</button>\n"""
    body2 += f"""
<div id="{country}" class="tabcontent">
  <iframe src="maps/pipes_map_{country}.html" width="100%" height="100%" loading="lazy"></iframe>
</div>

"""


html = header + body1 + body2 + footer

with open("all_pipeline_maps.html", "w", encoding="utf-8") as f:
    f.write(html)