/* =========================================================
   CARRITO DE COMPRAS - SANTA CLARA
   Módulo completo con persistencia en localStorage
   ========================================================= */

const Cart = (() => {
    const STORAGE_KEY = "santaclara-cart";
    const AUTO_CLOSE_MS = 2500;
    const listeners = new Set();

    // ---------- Utilidades ----------

    const formatPrice = (amount) => `S/ ${amount.toFixed(2)}`;

    const readCart = () => {
        try {
            const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
            return Array.isArray(stored) ? stored : [];
        } catch {
            return [];
        }
    };

    const saveCart = (items) => {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
        } catch {
            // El carrito sigue funcionando en memoria si el navegador bloquea el almacenamiento.
        }
        notify();
    };

    const notify = () => {
        const items = getItems();
        const count = getTotalItems();
        const total = getTotal();
        listeners.forEach((fn) => fn({ items, count, total }));
    };

    // ---------- API pública ----------

    const getItems = () => readCart();

    const getTotalItems = () => readCart().reduce((sum, item) => sum + item.quantity, 0);

    const getTotal = () =>
        readCart().reduce((sum, item) => sum + item.price * item.quantity, 0);

    const addItem = (product) => {
        const items = readCart();
        const existing = items.find((item) => item.id === product.id);

        if (existing) {
            existing.quantity = Math.min(99, existing.quantity + 1);
        } else {
            items.push({
                id: product.id,
                name: product.name,
                detail: product.detail,
                price: product.price,
                image: product.image,
                quantity: 1,
            });
        }

        saveCart(items);
        return { items, added: true };
    };

    const removeItem = (productId) => {
        const items = readCart().filter((item) => item.id !== productId);
        saveCart(items);
        return items;
    };

    const updateQuantity = (productId, quantity) => {
        const items = readCart();
        const item = items.find((i) => i.id === productId);

        if (item) {
            if (quantity <= 0) {
                return removeItem(productId);
            }
            item.quantity = Math.min(99, quantity);
            saveCart(items);
        }
        return items;
    };

    const clear = () => {
        saveCart([]);
    };

    const onChange = (fn) => {
        listeners.add(fn);
        return () => listeners.delete(fn);
    };

    // ---------- Renderizado del panel ----------

    const renderCartPanel = () => {
        const panel = document.getElementById("cart-panel");
        const itemsContainer = document.getElementById("cart-items");
        const totalElement = document.getElementById("cart-total");
        const countElement = document.getElementById("cart-count");
        const checkoutBtn = document.getElementById("cart-checkout");

        if (!panel || !itemsContainer || !totalElement || !countElement) return;

        const items = getItems();
        const total = getTotal();
        const count = getTotalItems();

        // Actualizar contador del navbar
        countElement.textContent = count;
        countElement.classList.toggle("hidden", count === 0);

        // Actualizar total
        totalElement.textContent = formatPrice(total);

        // Habilitar/deshabilitar botón de checkout
        if (checkoutBtn) {
            checkoutBtn.disabled = count === 0;
        }

        // Renderizar items
        if (items.length === 0) {
            itemsContainer.innerHTML = `
                <div class="flex flex-col items-center justify-center py-12 text-center">
                    <span class="text-4xl" aria-hidden="true">🛒</span>
                    <p class="mt-4 text-sm font-semibold text-navy">Tu carrito está vacío</p>
                    <p class="mt-1 text-xs text-slate-500">Agrega productos para comenzar</p>
                </div>
            `;
            return;
        }

        itemsContainer.innerHTML = items
            .map(
                (item) => `
            <div class="flex gap-4 rounded-xl border border-slate-100 bg-white p-3" data-cart-item="${item.id}">
                <img src="${item.image}" alt="${item.name}" class="h-16 w-16 rounded-lg object-cover" width="64" height="64">
                <div class="flex flex-1 flex-col">
                    <div>
                        <h4 class="text-sm font-bold text-navy">${item.name}</h4>
                        <p class="text-xs text-slate-500">${item.detail}</p>
                    </div>
                    <div class="mt-2 flex items-center justify-between">
                        <div class="flex items-center gap-2">
                            <button type="button" class="flex h-7 w-7 items-center justify-center rounded-full border border-slate-200 text-sm font-bold text-navy transition hover:bg-slate-50" data-cart-decrease="${item.id}" aria-label="Disminuir cantidad">−</button>
                            <span class="w-8 text-center text-sm font-semibold text-navy" data-cart-quantity="${item.id}">${item.quantity}</span>
                            <button type="button" class="flex h-7 w-7 items-center justify-center rounded-full border border-slate-200 text-sm font-bold text-navy transition hover:bg-slate-50" data-cart-increase="${item.id}" aria-label="Aumentar cantidad">+</button>
                        </div>
                        <span class="text-sm font-bold text-field">${formatPrice(item.price * item.quantity)}</span>
                    </div>
                    <button type="button" data-cart-remove="${item.id}" aria-label="Eliminar ${item.name} del carrito"
                        style="margin-top:10px;align-self:flex-start;display:inline-flex;align-items:center;gap:6px;padding:6px 12px;border-radius:999px;border:1px solid #ef4444;background:rgba(239,68,68,.12);color:#ef4444;font-size:12px;font-weight:700;cursor:pointer;">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/></svg>
                        Eliminar
                    </button>
                </div>
            </div>
        `,
            )
            .join("");
    };

    // ---------- Eventos ----------

    const init = () => {
        const toggleBtn = document.getElementById("cart-toggle");
        const panel = document.getElementById("cart-panel");
        const closeBtn = document.getElementById("cart-close");

        // --- Helpers para abrir/cerrar el panel ---
        const cancelAutoClose = () => {
            if (panel && panel._autoClose) {
                clearTimeout(panel._autoClose);
                panel._autoClose = null;
            }
        };

        const closePanel = () => {
            if (!panel) return;
            cancelAutoClose();
            panel.classList.add("hidden");
            toggleBtn?.setAttribute("aria-expanded", "false");
        };

        const openPanel = () => {
            if (!panel) return;
            cancelAutoClose();
            panel.classList.remove("hidden");
            toggleBtn?.setAttribute("aria-expanded", "true");
        };

        // Abre el panel y lo cierra solo a los pocos segundos
        const openPanelBriefly = () => {
            openPanel();
            panel._autoClose = setTimeout(closePanel, AUTO_CLOSE_MS);
        };

        // Toggle del panel
        if (toggleBtn && panel) {
            toggleBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                const isOpen = !panel.classList.contains("hidden");
                if (isOpen) {
                    closePanel();
                } else {
                    openPanel();
                    renderCartPanel();
                }
            });
        }

        if (closeBtn && panel) {
            closeBtn.addEventListener("click", closePanel);
        }

        // Si el usuario interactúa con el panel, no se cierra solo
        if (panel) {
            panel.addEventListener("mouseenter", cancelAutoClose);
            panel.addEventListener("focusin", cancelAutoClose);
        }

        // Cerrar al hacer clic fuera
        document.addEventListener("click", (e) => {
            if (panel && !panel.classList.contains("hidden")) {
                const esToggle =
                    toggleBtn?.contains(e.target) ||
                    e.target.closest("#cart-toggle-mobile");
                if (!panel.contains(e.target) && !esToggle) {
                    closePanel();
                }
            }
        });

        // Cerrar con Escape
        document.addEventListener("keydown", (e) => {
            if (e.key === "Escape" && panel && !panel.classList.contains("hidden")) {
                closePanel();
            }
        });

        // Eventos del carrito (delegación)
        document.addEventListener("click", (e) => {
            // ----- Agregar al carrito -----
            const addBtn = e.target.closest("[data-add-to-cart]");
            if (addBtn) {
                e.preventDefault();
                const product = {
                    id: addBtn.dataset.productId,
                    name: addBtn.dataset.productName,
                    detail: addBtn.dataset.productDetail,
                    price: parseFloat(addBtn.dataset.productPrice),
                    image: addBtn.dataset.productImage,
                };
                addItem(product);
                renderCartPanel();

                // Feedback visual (conserva el ícono y el texto traducido original)
                if (!addBtn.dataset.originalHtml) {
                    addBtn.dataset.originalHtml = addBtn.innerHTML;
                    addBtn.innerHTML = "✓ Agregado";
                }
                addBtn.classList.add("added-to-cart");

                clearTimeout(addBtn._feedbackTimer);
                addBtn._feedbackTimer = setTimeout(() => {
                    addBtn.classList.remove("added-to-cart");
                    if (addBtn.dataset.originalHtml) {
                        addBtn.innerHTML = addBtn.dataset.originalHtml;
                        delete addBtn.dataset.originalHtml;
                    }
                }, 1500);

                // Abrir el panel brevemente y cerrarlo solo
                openPanelBriefly();
                return;
            }

            // ----- Eliminar producto -----
            const removeBtn = e.target.closest("[data-cart-remove]");
            if (removeBtn) {
                removeItem(removeBtn.dataset.cartRemove);
                renderCartPanel();
                return;
            }

            // ----- Aumentar cantidad -----
            const increaseBtn = e.target.closest("[data-cart-increase]");
            if (increaseBtn) {
                const item = getItems().find((i) => i.id === increaseBtn.dataset.cartIncrease);
                if (item) {
                    updateQuantity(item.id, item.quantity + 1);
                    renderCartPanel();
                }
                return;
            }

            // ----- Disminuir cantidad -----
            const decreaseBtn = e.target.closest("[data-cart-decrease]");
            if (decreaseBtn) {
                const item = getItems().find((i) => i.id === decreaseBtn.dataset.cartDecrease);
                if (item) {
                    updateQuantity(item.id, item.quantity - 1);
                    renderCartPanel();
                }
            }
        });

        // Botón de checkout
        const checkoutBtn = document.getElementById("cart-checkout");
        if (checkoutBtn) {
            checkoutBtn.addEventListener("click", () => {
                const items = getItems();
                if (items.length === 0) return;

                // Guardar carrito en sesión para el formulario
                sessionStorage.setItem("santaclara-cart-checkout", JSON.stringify(items));

                // Redirigir al formulario
                window.location.href = checkoutBtn.dataset.checkoutUrl;
            });
        }

        // Escuchar cambios
        onChange(renderCartPanel);

        // Render inicial
        renderCartPanel();
    };

    // Inicializar cuando el DOM esté listo
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }

    return {
        getItems,
        getTotalItems,
        getTotal,
        addItem,
        removeItem,
        updateQuantity,
        clear,
        onChange,
        formatPrice,
    };
})();