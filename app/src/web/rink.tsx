import { useId, type ReactNode } from "react";

export default function Rink({
  children,
  label,
  description,
  className = "spatial-rink",
}: {
  readonly children: ReactNode;
  readonly label: string;
  readonly description: string;
  readonly className?: string;
}) {
  const id = useId();
  return (
    <svg
      className={className}
      viewBox="-1 -1 87 202"
      role="img"
      aria-labelledby={`${id}-title`}
      aria-describedby={`${id}-description`}
    >
      <title id={`${id}-title`}>{label}</title>
      <desc id={`${id}-description`}>{description}</desc>
      <defs>
        <clipPath id={`${id}-clip`}>
          <rect x="0" y="0" width="85" height="200" rx="28" />
        </clipPath>
      </defs>
      <g clipPath={`url(#${id}-clip)`}>
        {children}
        <g
          className="spatial-landmarks"
          fill="none"
          stroke="#64767b"
          strokeWidth="0.3"
        >
          <path d="M0 75H85M0 125H85M0 100H85" />
          <circle cx="42.5" cy="100" r="15" />
          <path d="M39.5 11H45.5M39.5 189H45.5" />
        </g>
      </g>
      <rect
        className="spatial-outline"
        x="0"
        y="0"
        width="85"
        height="200"
        rx="28"
        fill="none"
        stroke="#59676d"
        strokeWidth="0.6"
      />
    </svg>
  );
}
