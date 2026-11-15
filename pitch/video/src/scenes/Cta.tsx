// The call to action: the QR code on the slide's own paper, after the closing line.
import { Img, staticFile } from "remotion";

import { C } from "../theme";
import { Eyebrow, Headline, PixelLabel, Reveal, Slide, useSpring } from "../ui";

export function Cta({ duration }: { duration: number }) {
  const s = useSpring(10, 16);
  return (
    <Slide section="Try it" duration={duration}>
      <div style={{ position: "absolute", left: 160, top: 300, width: 900 }}>
        <Eyebrow delay={2}>Try it</Eyebrow>
        <Headline delay={6} size={96} style={{ marginTop: 18 }} lines={[["See", "4site"], [{ t: "for", color: C.blue }, { t: "yourself.", color: C.blue }]]} />
        <Reveal delay={24}>
          <p style={{ fontSize: 40, color: C.ink2, marginTop: 30 }}>Scan to explore 4site.</p>
        </Reveal>
        <Reveal delay={34}>
          <div style={{ display: "flex", alignItems: "center", gap: 18, marginTop: 50 }}>
            <Img src={staticFile("logo-flat.png")} style={{ height: 64, objectFit: "contain" }} />
            <PixelLabel size={18}>Risk intelligence for every site in New York</PixelLabel>
          </div>
        </Reveal>
      </div>
      <div style={{ position: "absolute", right: 200, top: 220, width: 620, height: 620, transform: `scale(${0.85 + 0.15 * s})`, opacity: s }}>
        <Img src={staticFile("qr.png")} style={{ width: "100%", height: "100%" }} />
      </div>
    </Slide>
  );
}
