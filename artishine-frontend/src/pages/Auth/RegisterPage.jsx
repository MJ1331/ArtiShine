// src/pages/RegisterPage.jsx
import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import API from "../../api"; // central axios instance
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import {
  GoogleMap,
  Marker,
  StandaloneSearchBox,
  useLoadScript,
} from "@react-google-maps/api";

// --- 1. IMPORT THE ANIMATED BACKGROUND ---
import AnimatedBackground from '../../components/AnimatedBackground';

const MAP_LIBRARIES = ["places"];
const MAP_CONTAINER_STYLE = { width: "100%", height: "320px", borderRadius: 12 };
const DEFAULT_CENTER = { lat: 20.5937, lng: 78.9629 }; // India center as default

/* ---------- MapPicker component (No Changes) ---------- */
function MapPicker({ apiKey, initialLocation = null, onLocationChange }) {
  const { isLoaded, loadError } = useLoadScript({
    googleMapsApiKey: apiKey,
    libraries: MAP_LIBRARIES,
  });

  const [marker, setMarker] = useState(initialLocation || DEFAULT_CENTER);
  const mapRef = useRef(null);
  const searchBoxRef = useRef(null);

  const onMapLoad = (map) => {
    mapRef.current = map;
  };

  const handleMapClick = (e) => {
    const newLoc = { lat: e.latLng.lat(), lng: e.latLng.lng() };
    setMarker(newLoc);
    onLocationChange?.(newLoc);
  };

  const handleMarkerDragEnd = (e) => {
    const newLoc = { lat: e.latLng.lat(), lng: e.latLng.lng() };
    setMarker(newLoc);
    onLocationChange?.(newLoc);
  };

  const handlePlacesChanged = () => {
    const places = searchBoxRef.current?.getPlaces();
    if (!places || places.length === 0) return;
    const place = places[0];
    if (!place.geometry) return;
    const newLoc = {
      lat: place.geometry.location.lat(),
      lng: place.geometry.location.lng(),
    };
    setMarker(newLoc);
    onLocationChange?.(newLoc);
    mapRef.current?.panTo(newLoc);
  };

  if (loadError) return <div className="p-3 text-red-600">Map failed to load</div>;
  if (!isLoaded) return <div className="p-3 text-amber-700">Loading map…</div>;

  return (
    <div className="space-y-3">
      <StandaloneSearchBox
        onLoad={(ref) => (searchBoxRef.current = ref)}
        onPlacesChanged={handlePlacesChanged}
      >
        <input
          type="text"
          placeholder="Search shop address..."
          className="w-full p-2 rounded-lg border border-amber-200 bg-white/60 focus:outline-none"
        />
      </StandaloneSearchBox>

      <div className="rounded-lg overflow-hidden border border-amber-100">
        <GoogleMap
          mapContainerStyle={MAP_CONTAINER_STYLE}
          zoom={12}
          center={marker}
          onLoad={onMapLoad}
          onClick={handleMapClick}
        >
          <Marker position={marker} draggable onDragEnd={handleMarkerDragEnd} />
        </GoogleMap>
      </div>

      <div className="text-xs text-amber-700">
        Lat: {Number(marker.lat).toFixed(6)} • Lng: {Number(marker.lng).toFixed(6)}
      </div>
    </div>
  );
}

/* ---------- helpers (No Changes) ---------- */
function formatDateToDDMMYYYY(dateString) {
  if (!dateString) return "";
  const [y, m, d] = dateString.split("-");
  return `${d}-${m}-${y}`;
}

/* ---------- main register page ---------- */
const RegisterPage = () => {
  const navigate = useNavigate();

  // form state (THIS IS THE FULL, CORRECT LIST)
  const [role, setRole] = useState("artisan");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [place, setPlace] = useState("");
  const [latitude, setLatitude] = useState(null);
  const [longitude, setLongitude] = useState(null);
  const [language, setLanguage] = useState("en-US");
  const [dateOfBirthInput, setDateOfBirthInput] = useState("");
  const [shopName, setShopName] = useState("");
  const [shopType, setShopType] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Vite env vars
  const GOOGLE_MAPS_API_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || "";

  // --- 2. REMOVE THE 'useEffect' THAT SETS 'bg-amber-50' ---
  /*
  useEffect(() => {
    document.body.classList.add("bg-amber-50");
    return () => document.body.classList.remove("bg-amber-50");
  }, []);
  */

  const handleLocationChange = (loc) => {
    setLatitude(Number(loc.lat));
    setLongitude(Number(loc.lng));
  };

  const validateForm = () => {
    if (!name.trim()) return "Please enter full name";
    if (!email.trim()) return "Please enter email";
    if (!password) return "Please enter password";
    if (password !== confirmPassword) return "Passwords do not match";
    if (!place.trim()) return "Please enter your place (city, region)";
    if (latitude === null || longitude === null) return "Please pick a location on the map";
    if (role === "artisan") {
      if (!language.trim()) return "Please select a language";
      if (!dateOfBirthInput) return "Please pick date of birth";
      if (!shopName.trim()) return "Please enter shop name";
      if (!shopType.trim()) return "Please enter shop type";
      if (!phoneNumber.trim()) return "Please enter phone number";
      if (!/^\+?[0-9]{7,15}$/.test(phoneNumber.trim()))
        return "Please enter a valid phone number (digits, 7-15 chars, optional +)";
    }
    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);
    try {
      if (role === "artisan") {
        const payload = {
          name: name.trim(),
          email: email.trim(),
          password,
          role: "artisan",
          place: place.trim(),
          latitude: Number(latitude),
          longitude: Number(longitude),
          language: language.trim(),
          date_of_birth: formatDateToDDMMYYYY(dateOfBirthInput),
          shop_name: shopName.trim(),
          shop_type: shopType.trim(),
          phone_number: phoneNumber.trim(),
        };

        // Use central axios instance (API)
        await API.post("/users/register", payload);

        toast.success("Artisan registered! Please login.", { position: "top-center", autoClose: 2000 });
        setTimeout(() => navigate("/login"), 1600);
      } else {
        const payload = {
          name: name.trim(),
          email: email.trim(),
          password,
          role: "buyer",
          place: place.trim(),
          latitude: Number(latitude),
          longitude: Number(longitude),
        };

        await API.post("/users/register-buyer", payload);

        toast.success("Buyer registered! Please login.", { position: "top-center", autoClose: 2000 });
        setTimeout(() => navigate("/login"), 1600);
      }
    } catch (err) {
      console.error(err);
      const message =
        err?.response?.data?.detail || err?.response?.data?.message || err.message || "Registration failed";
      setError(message);
      toast.error(message, { position: "top-center" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen overflow-hidden relative">
      
      {/* --- 3. ADD THE ANIMATED BACKGROUND COMPONENT --- */}
      <AnimatedBackground />

      {/* --- 4. REMOVE THE OLD 'bg-amber-...' BLOB DECORATIONS --- */}
      {/*
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-1/4 -left-20 w-96 h-96 bg-amber-200 rounded-full ..."></div>
        <div className="absolute top-1/2 -right-20 w-96 h-96 bg-amber-300 rounded-full ..."></div>
        <div className="absolute -bottom-20 left-1/4 w-96 h-96 bg-amber-400 rounded-full ..."></div>
      </div>
      */}

      <div className="relative z-10 min-h-screen flex items-center justify-center p-14">
        <motion.div
          className="w-full max-w-2xl bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl overflow-hidden"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          {/* --- ALL CODE BELOW IS UNCHANGED --- */}
          <div className="p-8">
            <div className="text-center mb-6">
              <motion.h1 className="text-4xl font-serif font-bold text-amber-900 mb-1" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                Join Artishine
              </motion.h1>
              <motion.p className="text-amber-700" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                Create your account to get started
              </motion.p>
            </div>

            {error && <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-lg text-sm">{error}</div>}

            <form onSubmit={handleSubmit} className="grid grid-cols-1 gap-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-amber-800 mb-1">Full name</label>
                  <input value={name} onChange={(e) => setName(e.target.value)} className="w-full px-4 py-2 rounded-lg border border-amber-200 bg-white/50" placeholder="e.g., Asha Devi" required />
                </div>
                <div>
                  <label className="block text-sm font-medium text-amber-800 mb-1">Email</label>
                  <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full px-4 py-2 rounded-lg border border-amber-200 bg-white/50" placeholder="you@example.com" required />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-amber-800 mb-1">Password</label>
                  <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full px-4 py-2 rounded-lg border border-amber-200 bg-white/50" placeholder="••••••••" required minLength={6} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-amber-800 mb-1">Confirm Password</label>
                  <input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} className="w-full px-4 py-2 rounded-lg border border-amber-200 bg-white/50" placeholder="••••••••" required minLength={6} />
                </div>
              </div>

              <div className="flex items-center gap-4">
                <label className="text-sm font-medium text-amber-800">Register as</label>
                <select value={role} onChange={(e) => setRole(e.target.value)} className="px-3 py-2 rounded-lg border border-amber-200 bg-white/50">
                  <option value="artisan">Artisan</option>
                  <option value="buyer">Buyer</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-amber-800 mb-1">Place (city / region)</label>
                <input value={place} onChange={(e) => setPlace(e.target.value)} className="w-full px-4 py-2 rounded-lg border border-amber-200 bg-white/50" placeholder="e.g., Jaipur, India" required />
              </div>

              <div>
                <label className="block text-sm font-medium text-amber-800 mb-2">Pick your location on map</label>
                <MapPicker apiKey={GOOGLE_MAPS_API_KEY} initialLocation={latitude !== null && longitude !== null ? { lat: latitude, lng: longitude } : null} onLocationChange={handleLocationChange} />
                <p className="text-xs text-amber-700 mt-2">Marker sets the shop location (lat/lng).</p>
              </div>

              {role === "artisan" && (
                <>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-amber-800 mb-1">Shop name</label>
                      <input value={shopName} onChange={(e) => setShopName(e.target.value)} className="w-full px-4 py-2 rounded-lg border border-amber-200 bg-white/50" placeholder="e.g., Asha Pottery" required />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-amber-800 mb-1">Shop type</label>
                      <input value={shopType} onChange={(e) => setShopType(e.target.value)} className="w-full px-4 py-2 rounded-lg border border-amber-200 bg-white/50" placeholder="e.g., Pottery, Textiles" required />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-amber-800 mb-1">Phone number</label>
                      <input value={phoneNumber} onChange={(e) => setPhoneNumber(e.target.value)} className="w-full px-4 py-2 rounded-lg border border-amber-200 bg-white/50" placeholder="+9198xxxxxxxx" required />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-amber-800 mb-1">Language (BCP-47)</label>
                      <select value={language} onChange={(e) => setLanguage(e.target.value)} className="w-full px-4 py-2 rounded-lg border border-amber-200 bg-white/50">
                        <option value="en-US">English (en-US)</option>
                        <option value="hi-IN">Hindi (hi-IN)</option>
                        <option value="bn-IN">Bengali (bn-IN)</option>
                        <option value="ta-IN">Tamil (ta-IN)</option>
                        <option value="te-IN">Telugu (te-IN)</option>
                        <option value="ml-IN">Malayalam (ml-IN)</option>
                        <option value="gu-IN">Gujarati (gu-IN)</option>
                        <option value="kn-IN">Kannada (kn-IN)</option>
                        <option value="pa-IN">Punjabi (pa-IN)</option>
                      </select>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-amber-800 mb-1">Date of birth</label>
                      <input type="date" value={dateOfBirthInput} onChange={(e) => setDateOfBirthInput(e.target.value)} className="w-full px-4 py-2 rounded-lg border border-amber-200 bg-white/50" max={new Date().toISOString().split("T")[0]} />
                      <div className="text-xs text-amber-600 mt-1">Will be sent to backend as DD-MM-YYYY.</div>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-amber-800 mb-1">(Optional) Extra contact</label>
                      <input className="w-full px-4 py-2 rounded-lg border border-amber-200 bg-white/50" placeholder="Optional notes" />
                    </div>
                  </div>
                </>
              )}

              <div className="pt-2">
                <button type="submit" disabled={loading} className={`w-full py-3 px-4 bg-amber-600 hover:bg-amber-700 text-white font-medium rounded-lg transition-colors ${loading ? "opacity-70 cursor-not-allowed" : ""}`}>
                  {loading ? "Creating Account..." : "Create Account"}
                </button>
              </div>
            </form>

            <div className="mt-6">
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-amber-200"></div>
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-2 bg-white text-amber-700">Already have an account?</span>
                </div>
              </div>

              <div className="mt-4">
                <button onClick={() => navigate("/login")} className="w-full flex justify-center py-2 px-4 border border-amber-200 rounded-lg shadow-sm bg-white text-sm font-medium text-amber-700 hover:bg-amber-50">Sign In</button>
              </div>
            </div>

            <ToastContainer />
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default RegisterPage;