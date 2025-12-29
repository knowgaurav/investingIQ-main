export default function Home() {
    return (
        <main className="min-h-screen bg-white">
            <div className="container mx-auto px-4 py-16">
                <div className="text-center">
                    <h1 className="text-4xl font-bold text-gray-900 mb-4">
                        InvestingIQ
                    </h1>
                    <p className="text-xl text-gray-600 mb-8">
                        AI-Powered Stock Analysis Platform
                    </p>

                    {/* Stock Search - To be implemented */}
                    <div className="max-w-xl mx-auto">
                        <div className="relative">
                            <input
                                type="text"
                                placeholder="Search for any stock (e.g., AAPL, TSLA, NVDA)..."
                                className="w-full px-6 py-4 text-lg border-2 border-gray-200 rounded-full focus:border-primary focus:outline-none"
                            />
                            <button className="absolute right-2 top-1/2 -translate-y-1/2 bg-primary text-white px-6 py-2 rounded-full hover:bg-blue-600 transition">
                                Analyze
                            </button>
                        </div>
                    </div>

                    <p className="mt-8 text-gray-500">
                        Powered by AI • Real-time Analysis • Any Stock Worldwide
                    </p>
                </div>
            </div>
        </main>
    )
}
