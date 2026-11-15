// A small inline icon set (1.5 px strokes on a 16 px grid) so the app needs no icon dependency.
import type { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement>;

function Icon({ children, ...props }: IconProps) {
  return (
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"
      strokeLinejoin="round" aria-hidden="true" {...props}>
      {children}
    </svg>
  );
}

export const SearchIcon = (p: IconProps) => (
  <Icon {...p}><circle cx="7" cy="7" r="4.5" /><path d="m10.5 10.5 3 3" /></Icon>
);
export const LayersIcon = (p: IconProps) => (
  <Icon {...p}><path d="m8 2 6 3.2L8 8.4 2 5.2 8 2Z" /><path d="m2 8.2 6 3.2 6-3.2" /><path d="m2 11 6 3.2 6-3.2" /></Icon>
);
export const ChatIcon = (p: IconProps) => (
  <Icon {...p}><path d="M2.5 4.5a2 2 0 0 1 2-2h7a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2H7l-3 2.5v-2.5h0a1.5 1.5 0 0 1-1.5-1.5v-5.5Z" /></Icon>
);
export const CloseIcon = (p: IconProps) => (
  <Icon {...p}><path d="m4 4 8 8M12 4l-8 8" /></Icon>
);
export const SunIcon = (p: IconProps) => (
  <Icon {...p}><circle cx="8" cy="8" r="3" /><path d="M8 1.5v1.5M8 13v1.5M1.5 8H3M13 8h1.5M3.4 3.4l1 1M11.6 11.6l1 1M3.4 12.6l1-1M11.6 4.4l1-1" /></Icon>
);
export const MoonIcon = (p: IconProps) => (
  <Icon {...p}><path d="M13 9.5A5.5 5.5 0 1 1 6.5 3a4.5 4.5 0 0 0 6.5 6.5Z" /></Icon>
);
export const InfoIcon = (p: IconProps) => (
  <Icon {...p}><circle cx="8" cy="8" r="6" /><path d="M8 7.2V11M8 5h0" /></Icon>
);
export const AlertIcon = (p: IconProps) => (
  <Icon {...p}><path d="M8 2.2 14.2 13H1.8L8 2.2Z" /><path d="M8 6.5v3M8 11.3h0" /></Icon>
);
export const PinIcon = (p: IconProps) => (
  <Icon {...p}><path d="M8 14s4.5-4.2 4.5-7.5a4.5 4.5 0 0 0-9 0C3.5 9.8 8 14 8 14Z" /><circle cx="8" cy="6.5" r="1.5" /></Icon>
);
export const KeyboardIcon = (p: IconProps) => (
  <Icon {...p}><rect x="1.5" y="4" width="13" height="8" rx="1.5" /><path d="M4 6.5h0M6.5 6.5h0M9 6.5h0M11.5 6.5h0M4.5 9.5h7" /></Icon>
);
export const LinkIcon = (p: IconProps) => (
  <Icon {...p}><path d="M6.5 9.5 9.5 6.5" /><path d="M7 4.5 8.2 3.3a2.6 2.6 0 0 1 3.7 3.7L10.7 8.2M9 11.5l-1.2 1.2a2.6 2.6 0 0 1-3.7-3.7L5.3 7.8" /></Icon>
);
export const ChevronIcon = (p: IconProps) => (
  <Icon {...p}><path d="m6 4 4 4-4 4" /></Icon>
);
