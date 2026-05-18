import { useEffect, useRef, useState } from "react";

export default function AnimatedNumber({
  value, duration = 800, prefix = "", suffix = ""
}) {
  const [display,  setDisplay]  = useState(0);
  const startTime  = useRef(null);
  const startValue = useRef(0);
  const frameRef   = useRef(null);

  const numericValue =
    parseFloat(String(value).replace(/[^0-9.]/g, "")) || 0;

  useEffect(() => {
    startValue.current = display;
    startTime.current  = null;

    const ease = (t) => 1 - Math.pow(1 - t, 3);

    const animate = (timestamp) => {
      if (!startTime.current) startTime.current = timestamp;
      const elapsed  = timestamp - startTime.current;
      const progress = Math.min(elapsed / duration, 1);
      const current  =
        startValue.current +
        (numericValue - startValue.current) * ease(progress);
      setDisplay(current);
      if (progress < 1)
        frameRef.current = requestAnimationFrame(animate);
    };

    frameRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frameRef.current);
  }, [numericValue]);

  const formatted =
    numericValue >= 1_000_000
      ? `${(display / 1_000_000).toFixed(1)}M`
      : numericValue >= 1_000
      ? `${(display / 1_000).toFixed(0)}K`
      : display.toFixed(numericValue % 1 !== 0 ? 2 : 0);

  return <span>{prefix}{formatted}{suffix}</span>;
}
