export default function App() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="p-8 rounded-xl shadow-lg bg-white text-center">
        <h1 className="text-4xl font-bold text-blue-600 mb-4">
          ¡Hola Tailwind v4!
        </h1>
        <p className="text-gray-700">
          Este es tu primer componente con estilos de Tailwind v4 en React + Vite.
        </p>
        <button className="mt-6 px-6 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition">
          Click aquí
        </button>
      </div>
    </div>
  )
}
