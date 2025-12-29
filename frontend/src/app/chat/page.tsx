export default function ChatPage() {
    return (
        <main className="min-h-screen bg-gray-50">
            <div className="container mx-auto px-4 py-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-6">
                    AI Financial Assistant
                </h1>

                {/* Chat Interface - To be implemented */}
                <div className="max-w-3xl mx-auto">
                    <div className="bg-white rounded-lg shadow h-[600px] flex flex-col">
                        {/* Messages */}
                        <div className="flex-1 p-6 overflow-y-auto">
                            <div className="text-center text-gray-500 mt-20">
                                <p className="text-lg">Ask me anything about stocks!</p>
                                <p className="text-sm mt-2">
                                    Try: "Why did AAPL drop today?" or "What's the outlook for NVDA?"
                                </p>
                            </div>
                        </div>

                        {/* Input */}
                        <div className="border-t p-4">
                            <div className="flex gap-2">
                                <input
                                    type="text"
                                    placeholder="Ask about any stock..."
                                    className="flex-1 px-4 py-2 border rounded-lg focus:border-primary focus:outline-none"
                                />
                                <button className="bg-primary text-white px-6 py-2 rounded-lg hover:bg-blue-600 transition">
                                    Send
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    )
}
