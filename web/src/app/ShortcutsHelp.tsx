// The "?" overlay: every keyboard shortcut in one place.
import { Kbd, Panel } from "../design";
import { keyLabel, type Shortcut } from "./shortcuts";

export function ShortcutsHelp({ open, onClose, shortcuts }: { open: boolean; onClose: () => void; shortcuts: Shortcut[] }) {
  if (!open) return null;
  return (
    <div className="fs-cmd-scrim" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <Panel title="Keyboard shortcuts" onClose={onClose} className="fs-help" label="Keyboard shortcuts">
        <dl className="fs-help__list">
          {shortcuts.map((s) => (
            <div key={s.label}>
              <dt>{s.label}</dt>
              <dd>
                {s.keys.map((k, i) => (
                  <span key={k}>
                    {i > 0 && <span className="fs-help__or">or</span>}
                    {keyLabel(k)
                      .split(" ")
                      .map((part) => (
                        <Kbd key={part}>{part}</Kbd>
                      ))}
                  </span>
                ))}
              </dd>
            </div>
          ))}
        </dl>
      </Panel>
    </div>
  );
}
