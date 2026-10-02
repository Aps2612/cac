import { Nav } from "./sections/Nav";
import { Hero } from "./sections/Hero";
import { Problem } from "./sections/Problem";
import { NoAction } from "./sections/NoAction";
import { HowItWorks } from "./sections/HowItWorks";
import { Example } from "./sections/Example";
import { Benefits } from "./sections/Benefits";
import { Tools } from "./sections/Tools";
import { BookDemo } from "./sections/BookDemo";
import { Footer } from "./sections/Footer";

export default function App() {
  return (
    <>
      <Nav />
      <main id="main">
        <Hero />
        <Problem />
        <NoAction />
        <HowItWorks />
        <Example />
        <Benefits />
        <Tools />
        <BookDemo />
      </main>
      <Footer />
    </>
  );
}
