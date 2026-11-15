import { useId, type ReactNode } from "react";

export default function Rink({
  children,
  label,
  description,
  className = "spatial-rink",
  orientation = "portrait",
  onPoint,
}: {
  readonly children: ReactNode;
  readonly label: string;
  readonly description: string;
  readonly className?: string;
  readonly orientation?: "portrait" | "goalie";
  readonly onPoint?: (x: number, y: number) => void;
}) {
  const id = useId();
  return (
    <svg
      className={className}
      viewBox={orientation === "goalie" ? "-1 -1 202 87" : "-1 -1 87 202"}
      onPointerMove={
        onPoint
          ? (event) => {
              const matrix = event.currentTarget.getScreenCTM();
              if (!matrix) return;
              const point = event.currentTarget.createSVGPoint();
              point.x = event.clientX;
              point.y = event.clientY;
              const local = point.matrixTransform(matrix.inverse());
              onPoint(local.x, local.y);
            }
          : undefined
      }
      role="img"
      aria-labelledby={`${id}-title`}
      aria-describedby={`${id}-description`}
    >
      <title id={`${id}-title`}>{label}</title>
      <desc id={`${id}-description`}>{description}</desc>
      <defs>
        <clipPath id={`${id}-clip`}>
          <rect
            x="0"
            y="0"
            width={orientation === "goalie" ? 200 : 85}
            height={orientation === "goalie" ? 85 : 200}
            rx="28"
          />
        </clipPath>
      </defs>
      <g clipPath={`url(#${id}-clip)`}>
        {children}
        <g
          className="spatial-landmarks"
          fill="none"
          stroke="#64767b"
          strokeWidth="0.3"
          transform={
            orientation === "goalie" ? "matrix(0,1,1,0,0,0)" : undefined
          }
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
        width={orientation === "goalie" ? 200 : 85}
        height={orientation === "goalie" ? 85 : 200}
        rx="28"
        fill="none"
        stroke="#59676d"
        strokeWidth="0.6"
      />
    </svg>
  );
}
