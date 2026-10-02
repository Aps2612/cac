import { Nav } from "./sections/Nav";
import { Hero } from "./sections/Hero";
import { Problem } from "./sections/Problem";
import { Decisioning } from "./sections/Decisioning";
import { CustomerState } from "./sections/CustomerState";
import { Value } from "./sections/Value";
import { Stack } from "./sections/Stack";
import { HowItWorks } from "./sections/HowItWorks";
import { ForD2C } from "./sections/ForD2C";
import { UseCases } from "./sections/UseCases";
import { Incrementality } from "./sections/Incrementality";
import { Pilot } from "./sections/Pilot";
import { Contact } from "./sections/Contact";
import { About } from "./sections/About";
import { Footer } from "./sections/Footer";

export default function App() {
  return (
    <>
      <Nav />
      <main id="main">
        <Hero />
        <Problem />
        <Decisioning />
        <CustomerState />
        <Value />
        <Stack />
        <HowItWorks />
        <ForD2C />
        <UseCases />
        <Incrementality />
        <Pilot />
        <About />
        <Contact />
      </main>
      <Footer />
    </>
  );
}
