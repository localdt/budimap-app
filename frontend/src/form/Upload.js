import React, { useState } from 'react';
import axios from 'axios';
import { toast } from "react-toastify";
import { MapContainer, TileLayer, useMapEvents } from "react-leaflet";
import L from "leaflet";
import { useNavigate } from 'react-router-dom'
import { LoaderCircle } from 'lucide-react';

import "leaflet/dist/leaflet.css";

const icon = L.icon({
  iconSize: [25, 41],
  iconAnchor: [10, 41],
  popupAnchor: [2, -40],
  iconUrl: "https://unpkg.com/leaflet@1.6/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.6/dist/images/marker-shadow.png",
});

const latitude = -8.08915093091523;
const longitude = -34.79692857333338;

function MyComponent({ marker, setMarker, setUploadForm }) {
  const map = useMapEvents({
    click: (e) => {
      const { lat, lng } = e.latlng;
      if (marker) {
        map.removeLayer(marker);
      }
      const newMarker = L.marker([lat, lng], { icon }).addTo(map);
      setMarker(newMarker);
      setUploadForm((prevForm) => ({
        ...prevForm,
        latitude: lat,
        longitude: lng,
      }));
    },
  });
  return null;
}

export default function Upload(props) {
  const navigate = useNavigate();
  const [marker, setMarker] = useState(null);
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploadForm, setUploadForm] = useState({
    latitude: "",
    longitude: "",
  });

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    const formData = new FormData();
    files.forEach(file => {
      formData.append('file_uploads', file);
    });
    formData.append("latitude", uploadForm.latitude);
    formData.append("longitude", uploadForm.longitude);

    try {
      const response = await axios.post("http://localhost:8000/sightings/upload", formData);
      if (response.data.result === 0) {
        toast.success(response.data.detail);
      } else if (response.data.result === 1) {
        toast.warning(response.data.detail);
      } else {
        toast.error(response.data.detail);
      }
      setTimeout(() => {
        navigate("/sighting");
      }, 1000);
    } catch (error) {
      console.log(error);
      toast.error(error.response?.data?.detail || "Erro no envio");
    } finally {
      setLoading(false);
    }
  };

  const handleFileInputChange = (event) => {
    setFiles(Array.from(event.target.files));
  };

  const onChangeForm = (label, event) => {
    setUploadForm((prevForm) => ({
      ...prevForm,
      [label]: event.target.value,
    }));
  };

  return (
    <React.Fragment>
      <div className="min-h-screen bg-blue-400 flex justify-center items-center">
        <div className="container mx-auto max-w-screen-lg h-full py-12 px-12 bg-white rounded-2xl shadow-xl z-20">
          <div>
            <h1 className="text-3xl font-bold text-center mb-4 cursor-pointer">
              Cadastrar Avistamento
            </h1>
            <p className="w-100 text-center text-sm mb-8 font-semibold text-gray-700 tracking-wide cursor-pointer mx-auto">
              Informe a localização e selecione as imagens dos budiões avistados:
            </p>
          </div>
          <MapContainer
            className="Map"
            center={{ lat: latitude, lng: longitude }}
            zoom={5}
            scrollWheelZoom={false}
            style={{ height: "40vh" }}
          >
            <TileLayer
              attribution='&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <MyComponent marker={marker} setMarker={setMarker} setUploadForm={setUploadForm} />
          </MapContainer>

          <br />
          <form onSubmit={handleSubmit}>
            <div className="space-y-4">
              <input
                placeholder="Latitude"
                className="text-sm py-3 px-4 rounded-lg w-full border outline-none focus:ring focus:outline-none focus:ring-blue-400"
                type="text"
                value={uploadForm.latitude}
                onChange={(event) => onChangeForm("latitude", event)}
              />
              <input
                placeholder="Longitude"
                className="text-sm py-3 px-4 rounded-lg w-full border outline-none focus:ring focus:outline-none focus:ring-blue-400"
                type="text"
                value={uploadForm.longitude}
                onChange={(event) => onChangeForm("longitude", event)}
              />
              <input
                className="block text-sm py-3 px-4 rounded-lg w-full border outline-none focus:ring focus:outline-none focus:ring-blue-400"
                type="file"
                onChange={handleFileInputChange}
                multiple
                required
                onInvalid={(event) =>
                  event.currentTarget.setCustomValidity('Selecione as imagens')
                }
              />
            </div>
            <div className="mt-6 flex justify-center items-center">
              <button
                type="submit"
                disabled={loading}
                className="flex justify-center items-center gap-2 py-3 w-64 text-xl text-white bg-blue-400 rounded-2xl hover:bg-blue-300 active:bg-blue-500 outline-none"
              >
                {loading ? (
                  <>
                    <LoaderCircle className="animate-spin" size={24} />
                    Enviando...
                  </>
                ) : (
                  "Enviar"
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </React.Fragment>
  );
}

/*
import React, { useState } from 'react';
import axios from 'axios';
import { toast } from "react-toastify";
import { MapContainer, TileLayer, useMapEvents } from "react-leaflet";
import L from "leaflet";
import { useNavigate } from 'react-router-dom'

import "leaflet/dist/leaflet.css";

const icon = L.icon({
  iconSize: [25, 41],
  iconAnchor: [10, 41],
  popupAnchor: [2, -40],
  iconUrl: "https://unpkg.com/leaflet@1.6/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.6/dist/images/marker-shadow.png",
});

const latitude = -8.08915093091523;
const longitude = -34.79692857333338;


function MyComponent({ marker, setMarker, setUploadForm }) {
  const map = useMapEvents({
    click: (e) => {
      const { lat, lng } = e.latlng;

      // Remove previous marker
      if (marker) {
        map.removeLayer(marker);
      }

      // Create a new marker and set it to state
      const newMarker = L.marker([lat, lng], { icon }).addTo(map);
      setMarker(newMarker);

      // Update latitude and longitude in the form
      setUploadForm((prevForm) => ({
        ...prevForm,
        latitude: lat,
        longitude: lng,
      }));
    },
  });
  return null;
}

export default function Upload(props) {
  const navigate = useNavigate(); // Create a navigate function
  const [marker, setMarker] = useState(null); // state for the marker
  const [files, setFiles] = useState([]);
  const [uploadForm, setUploadForm] = useState({
    latitude: "",
    longitude: "",
  });

  const handleSubmit = async (event) => {
    event.preventDefault();
    const formData = new FormData();
    files.forEach(file => {
      formData.append('file_uploads', file);
    });
    formData.append("latitude", uploadForm.latitude);
    formData.append("longitude", uploadForm.longitude);

    await axios
      .post("http://localhost:8000/sightings/upload", formData)
      .then((response) => {
        console.log(response);
        if (response.data.result == 0) {
          toast.success(response.data.detail);
        } else if (response.data.result == 1) {
          toast.warning(response.data.detail);
        } else {
          toast.error(response.data.detail);
        }
          
        
        setTimeout(() => {
          navigate("/sighting")
        }, 1000);
      })
      .catch((error) => {
        console.log(error);
        toast.error(error.response.data.detail);
      });
  };

  const handleFileInputChange = (event) => {
    setFiles(Array.from(event.target.files));
  };

  const onChangeForm = (label, event) => {
    setUploadForm((prevForm) => ({
      ...prevForm,
      [label]: event.target.value,
    }));
  };

  return (
    <React.Fragment>
      <div className="min-h-screen bg-blue-400 flex justify-center items-center">
        <div className="container mx-auto max-w-screen-lg h-full py-12 px-12 bg-white rounded-2xl shadow-xl z-20">
          <div>
            <h1 className="text-3xl font-bold text-center mb-4 cursor-pointer">
              Cadastrar Avistamento
            </h1>
            <p className="w-100 text-center text-sm mb-8 font-semibold text-gray-700 tracking-wide cursor-pointer mx-auto">
              Informe a localização e selecione as imagens dos budiões avistados:
            </p>
          </div>
          <div>
            <div>
              <MapContainer
                className="Map"
                center={{ lat: latitude, lng: longitude }}
                zoom={5}
                scrollWheelZoom={false}
                style={{ height: "40vh" }}
              >
                <TileLayer
                  attribution='&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                <MyComponent marker={marker} setMarker={setMarker} setUploadForm={setUploadForm} />
              </MapContainer>
            </div>
          </div>
          <br />
          <form onSubmit={handleSubmit}>
            <div className="space-y-4">
              <input
                placeholder="Latitude"
                className="read-only:block text-sm py-3 px-4 rounded-lg w-full border outline-none focus:ring focus:outline-none focus:ring-blue-400"
                type="text"
                value={uploadForm.latitude}
                onChange={(event) => onChangeForm("latitude", event)}
                
              />
              <input
                placeholder="Longitude"
                className="read-only:block text-sm py-3 px-4 rounded-lg w-full border outline-none focus:ring focus:outline-none focus:ring-blue-400"
                type="text"
                value={uploadForm.longitude}
                onChange={(event) => onChangeForm("longitude", event)}
                
              />
              <input
                className="block text-sm py-3 px-4 rounded-lg w-full border outline-none focus:ring focus:outline-none focus:ring-blue-400"
                type="file"
                onChange={handleFileInputChange}
                multiple
                required
                onInvalid={(event) =>
                  event.currentTarget.setCustomValidity('Selecione as imagens')
                }
              />
            </div>
            <div className="text-center mt-6">
              <button
                type="submit"
                className="py-3 w-64 text-xl text-white bg-blue-400 rounded-2xl hover:bg-blue-300 active:bg-blue-500 outline-none"
              >
                Enviar
              </button>
            </div>
          </form>
        </div>
      </div>
    </React.Fragment>
  );
}
*/