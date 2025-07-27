import { APIKeyManagement } from './components/apikeys/APIKeyManagement'

function App() {
  return (
    <div className="min-h-screen bg-gray-100">
      <div className="container mx-auto py-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Multi-Bot RAG Platform
          </h1>
          <p className="text-lg text-gray-600">
            API Key Management Demo
          </p>
        </div>

        <APIKeyManagement />
      </div>
    </div>
  )
}

export default App