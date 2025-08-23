"use client";
import axios from "axios";
import { useState } from "react";
import SpeechRecognition, {
  useSpeechRecognition,
} from "react-speech-recognition";

const SpeechButton = () => {
  const { transcript, listening, resetTranscript } = useSpeechRecognition();

  const [loadingResponse, setLoadingResponse] = useState<boolean>(false);
  // TODO: plug error message in state and display
  const [errorMessage, setErrorMessage] = useState<string>();
  const [recommendationText, setRecommendationText] = useState<string>("");
  const [rationaleText, setRationaleText] = useState<string>("");

  const getAiResponse = async () => {
    console.log("running ai response");
    try {
      setLoadingResponse(true);
      const inputJSON = {
        text: transcript,
      };
      const rationaleInput = {
        query: transcript,
      };
      console.log(inputJSON);
      // TODO: use the given API to interact with AI
      const recommendResponse = await axios.post(
        "http://localhost:8000/api/stock-recommendation",
        inputJSON
      );
      const rationaleResponse = await axios.post(
        "http://localhost:8001/analyze",
        rationaleInput
      );

      setRecommendationText(recommendResponse.data.recommendation);
      setRationaleText(rationaleResponse.data.rationale);
    } catch (error) {
      console.log("error:", error);
    } finally {
      setLoadingResponse(false);
    }
  };

  const onClickStop = async () => {
    SpeechRecognition.stopListening();
    await getAiResponse();
  };

  return (
    <div className="mt-10 gap-3 flex flex-col items-center justify-center">
      <p>Talk to Finpal and get feedback on your portfolio</p>
      <p>Microphone: {listening ? "on" : "off"}</p>
      <div className="flex gap-2">
        <button
          onClick={() => SpeechRecognition.startListening()}
          className={`px-3 p-1 bg-white rounded-3xl text-black`}
        >
          Start
        </button>
        <button
          onClick={onClickStop}
          className="px-3 p-1 bg-white rounded-3xl text-black"
        >
          Stop
        </button>
        <button
          onClick={resetTranscript}
          className="px-3 p-1 bg-white rounded-3xl text-black"
        >
          Reset
        </button>
      </div>
      <p className="mt-5">Voice Input</p>
      <p>{transcript}</p>
      <div className="mt-5 max-w-4xl">
        {loadingResponse ? (
          <div className="text-center">
            <p className="text-lg animate-pulse">🤖 Analyzing...</p>
          </div>
        ) : (
          <>
            {recommendationText && rationaleText && (
              <div className="space-y-6">
                {/* Recommendation Section */}
                <div className="bg-gray-900 rounded-lg p-6 border border-gray-700">
                  <h2 className="text-xl font-semibold mb-4 text-blue-400">📊 Investment Analysis</h2>
                  <div className="text-gray-300 whitespace-pre-line leading-relaxed">
                    {recommendationText.replace(/\\n/g, '\n').replace(/\\t/g, '  ')}
                  </div>
                </div>

                {/* Rationale Section */}
                <div className="bg-gray-900 rounded-lg p-6 border border-gray-700">
                  <h2 className="text-xl font-semibold mb-4 text-green-400">💡 Market Sentiment</h2>
                  <div className="text-gray-300 leading-relaxed">
                    {(() => {
                      try {
                        // Extract JSON from the nested structure
                        const jsonMatch = rationaleText.match(/json\s*\n?\s*(\{.*\})/s);
                        if (jsonMatch) {
                          const parsedJson = JSON.parse(jsonMatch[1]);
                          const reasoning = parsedJson.reasoning || parsedJson.rationale || '';
                          const recommendation = parsedJson.recommendation || '';
                          return (
                            <div className="space-y-3">
                              {recommendation && (
                                <div className="flex items-center gap-2">
                                  <span className="font-semibold text-yellow-400">Recommendation:</span>
                                  <span className="px-3 py-1 bg-yellow-400/20 rounded-full text-yellow-300 font-medium">
                                    {recommendation.toUpperCase()}
                                  </span>
                                </div>
                              )}
                              <div className="text-gray-300">
                                {reasoning}
                              </div>
                            </div>
                          );
                        }
                        // Fallback if JSON parsing fails
                        return rationaleText.replace(/json\s*\n?\s*{[^}]*}/, '').replace(/\\n/g, ' ').trim();
                      } catch (e) {
                        // If all parsing fails, show cleaned text
                        return rationaleText.replace(/json\s*\n?\s*{[^}]*}/, '').replace(/\\n/g, ' ').trim();
                      }
                    })()}
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default SpeechButton;
