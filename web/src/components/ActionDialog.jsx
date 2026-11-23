import React, { createContext, forwardRef, useImperativeHandle, useRef, useState } from 'react';

export const DialogContext = createContext(null);
export const ActionDialog = forwardRef(function ActionDialog({ title, label, children, wide = false, busy = false }, ref) {
    const dialog = useRef(null);
    const [formBusy, setFormBusy] = useState(false);
    const pending = busy || formBusy;
    function open() {
        dialog.current.showModal();
        dialog.current.querySelector('input:not([type="hidden"]):not([type="file"]), select, textarea')?.focus();
    }
    function close() { dialog.current.close(); }
    useImperativeHandle(ref, () => ({ open, close }), []);
    return <>
        {label && <button type="button" onClick={open} className="ui-button">{label}</button>}
        <dialog ref={dialog} className={`action-dialog ${wide ? 'action-dialog-wide' : ''}`} aria-label={title} onClose={e => e.stopPropagation()} onCancel={e => { if (pending) e.preventDefault(); }} onClick={e => {
            if (e.target === e.currentTarget && !pending) {
                const r = e.currentTarget.getBoundingClientRect();
                if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) close();
            }
        }}>
            <header className="flex justify-between items-start gap-4 mb-6"><h2 className="text-xl font-bold">{title}</h2><button type="button" disabled={pending} aria-label="Fechar janela" onClick={close} className="text-2xl leading-none text-slate-300">×</button></header>
            <DialogContext.Provider value={{ setBusy: setFormBusy, close }}>{children}</DialogContext.Provider>
        </dialog>
    </>;
});
