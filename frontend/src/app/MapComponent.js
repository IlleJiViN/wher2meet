'use client';

import { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix Leaflet's default icon missing issue in Webpack/Next
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Custom Icons
const originIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

const resultIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

// Component to dynamically adjust map bounds based on markers
function MapBounds({ origins, results }) {
  const map = useMap();
  useEffect(() => {
    if (!map) return;
    const points = [];
    if (origins) origins.forEach(o => points.push([o.latitude, o.longitude]));
    if (results) results.forEach(r => points.push([r.latitude, r.longitude]));
    
    if (points.length > 0) {
      const bounds = L.latLngBounds(points);
      map.fitBounds(bounds, { padding: [40, 40] });
    }
  }, [map, origins, results]);
  return null;
}

export default function MapComponent({ origins, results }) {
  // Default center to Seoul if empty
  const defaultCenter = origins && origins.length > 0 
    ? [origins[0].latitude, origins[0].longitude] 
    : [37.5665, 126.9780];
  
  return (
    <div className="w-full h-[320px] rounded-2xl overflow-hidden shadow-md border border-gray-200 z-0 relative">
      <MapContainer center={defaultCenter} zoom={12} style={{ height: '100%', width: '100%', zIndex: 0 }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        {origins && origins.map((o) => (
          <Marker key={`origin-${o.id}`} position={[o.latitude, o.longitude]} icon={originIcon}>
            <Popup>
              <b>{o.name}</b><br/>(가중치 {o.weight}x)
            </Popup>
          </Marker>
        ))}
        
        {results && results.map((r, idx) => (
          <Marker key={`result-${r.place_id}`} position={[r.latitude, r.longitude]} icon={resultIcon}>
            <Popup>
              <div className="text-center">
                <span className="bg-red-100 text-red-600 font-bold px-1 rounded mr-1">{idx + 1}위</span>
                <b>{r.name}</b><br/>
                <span className="text-xs text-gray-500">{r.category}</span>
              </div>
            </Popup>
          </Marker>
        ))}
        
        <MapBounds origins={origins} results={results} />
      </MapContainer>
    </div>
  );
}
