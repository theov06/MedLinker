// Finder/components/MapView.jsx
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";

// SIMPLE VERSION - Just basic map with satellite imagery
export default function MapView({ facilities, selectedFacility, onSelectFacility }) {
    // Default to USA center
    const center = [39.8283, -98.5795];
    const zoom = 4;

    return (
        <div className="flex-1 border border-main rounded-lg overflow-hidden" style={{ height: "600px" }}>
            <MapContainer
                center={center}
                zoom={zoom}
                style={{ height: "100%", width: "100%" }}
                className="rounded-lg"
            >
                {/* Satellite imagery from Esri */}
                <TileLayer
                    url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                    attribution='Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
                />

                {/* Optional: Add street labels overlay */}
                <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    opacity={0.5}
                />

                {/* Simple markers */}
                {facilities.map((facility) => (
                    <Marker
                        key={facility.id}
                        position={[facility.lat, facility.lng]}
                        eventHandlers={{
                            click: () => onSelectFacility(facility),
                        }}
                    >
                        <Popup>
                            <div className="p-2">
                                <h3 className="font-semibold text-sm">{facility.name}</h3>
                                <p className="text-xs text-gray-600">{facility.specialty}</p>
                                <div className="mt-1 text-xs">
                                    <div>Status: <span className="font-medium capitalize">{facility.status}</span></div>
                                    <div>Doctors: <span className="font-medium">{facility.doctors}</span></div>
                                </div>
                            </div>
                        </Popup>
                    </Marker>
                ))}
            </MapContainer>
        </div>
    );
}