import Image from "next/image";
import SpeechButton from "./components/SpeechButton";

export default function Home() {

  return (
    <div className="py-10 flex flex-col items-center justify-center">
      <h1 className="my-2">Finpal</h1>
      <SpeechButton />
    </div>
  );
}
