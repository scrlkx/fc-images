figma.showUI(__html__, { width: 400, height: 270 });

figma.ui.postMessage({
  type: "pages",
  pages: figma.root.children.map((p) => p.name),
});

const SLIDE_W = 1080;
const SLIDE_H = 1440;
const GAP = 100;

function progress(text) {
  figma.ui.postMessage({ type: "progress", text });
}

function findByName(node, name) {
  if (node.name === name) return node;
  if ("children" in node) {
    for (const child of node.children) {
      const found = findByName(child, name);
      if (found) return found;
    }
  }
  return null;
}

function findImageNode(node) {
  if ("fills" in node && Array.isArray(node.fills) && node.fills.some((f) => f.type === "IMAGE")) {
    return node;
  }
  if ("children" in node) {
    for (const child of node.children) {
      const found = findImageNode(child);
      if (found) return found;
    }
  }
  return null;
}

function base64ToUint8Array(base64) {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

function replaceProductImage(coverNode, dataUrl) {
  const base64 = dataUrl.split(",")[1];
  const bytes = base64ToUint8Array(base64);
  const image = figma.createImage(bytes);
  const imageNode = findImageNode(coverNode);
  if (!imageNode) return;
  const fills = imageNode.fills.map((f) => {
    if (f.type === "IMAGE") return Object.assign({}, f, { imageHash: image.hash, scaleMode: "FIT" });
    return f;
  });
  imageNode.fills = fills;
}

async function updateSlide2(slide2Clone, product) {
  // Cover image
  const cover = findByName(slide2Clone, "Cover");
  if (cover) replaceProductImage(cover, product.image_b64);

  // Product name — first child of Details
  const details = findByName(slide2Clone, "Details");
  if (details && details.children.length > 0) {
    const nameNode = details.children[0];
    if (nameNode.type === "TEXT") {
      nameNode.characters = product.name;
    }
  }

  // Price nodes — children of Price
  const price = findByName(slide2Clone, "Price");
  if (price && price.children.length >= 2) {
    const prevNode = price.children[0];
    const newNode = price.children[1];

    if (prevNode.type === "TEXT") {
      const prevText = `de R$ ${product.prev_price} por apenas`;
      prevNode.characters = prevText;
      const strikeEnd = `de R$ ${product.prev_price}`.length;
      prevNode.setRangeTextDecoration(0, strikeEnd, "STRIKETHROUGH");
      prevNode.setRangeTextDecoration(strikeEnd, prevText.length, "NONE");
    }

    if (newNode.type === "TEXT") {
      newNode.characters = `R$ ${product.new_price}`;
    }
  }
}

figma.ui.onmessage = async (msg) => {
  if (msg.type !== "generate") return;

  const payload = msg.payload;

  try {
    // 1. Find target page
    const pageName = msg.page_name;
    progress(`Searching for page "${pageName}"…`);
    const page = figma.root.children.find((p) => p.name === pageName);
    if (!page) throw new Error(`Page "${pageName}" not found.`);

    // 2. Get template frame (first frame child of the page)
    const templateFrame = page.children.find((c) => c.type === "FRAME");
    if (!templateFrame) throw new Error("No template frame found on the page.");

    const slide1Template = templateFrame.children.find((c) => c.name === "Slide 1");
    if (!slide1Template) throw new Error('Slide 1 not found in the template frame.');

    const slide2Template = templateFrame.children.find((c) => c.name === "Slide 2");
    if (!slide2Template) throw new Error('Slide 2 not found in the template frame.');

    // 3. Load fonts
    progress("Loading fonts…");
    await Promise.all([
      figma.loadFontAsync({ family: "DM Sans", style: "Regular" }),
      figma.loadFontAsync({ family: "DM Sans", style: "Black" }),
    ]);

    // 4. Switch to target page and create parent frame
    figma.currentPage = page;

    const parentFrame = figma.createFrame();
    parentFrame.name = payload.frame_name;
    parentFrame.resize(
      (payload.products.length + 1) * SLIDE_W + payload.products.length * GAP,
      SLIDE_H
    );
    parentFrame.fills = [];
    parentFrame.clipsContent = false;

    // Position below the last existing frame on the page
    const existingFrames = page.children.filter((c) => c.type === "FRAME" && c !== parentFrame);
    if (existingFrames.length > 0) {
      const last = existingFrames[existingFrames.length - 1];
      parentFrame.x = last.x;
      parentFrame.y = last.y + last.height + 200;
    }

    // 5. Clone Slide 1 → update validity text
    progress("Creating Slide 1…");
    const slide1Clone = slide1Template.clone();
    parentFrame.appendChild(slide1Clone);
    slide1Clone.x = 0;
    slide1Clone.y = 0;

    const rules1 = findByName(slide1Clone, "Rules 1");
    if (rules1 && rules1.type === "TEXT") {
      rules1.characters = payload.validity_text;
    }

    // 6. Clone Slide 2 for each product
    for (let i = 0; i < payload.products.length; i++) {
      const product = payload.products[i];
      progress(`Creating slide ${i + 1}/${payload.products.length}: ${product.name}…`);

      const slide2Clone = slide2Template.clone();
      parentFrame.appendChild(slide2Clone);
      slide2Clone.x = (i + 1) * (SLIDE_W + GAP);
      slide2Clone.y = 0;

      await updateSlide2(slide2Clone, product);
    }

    // 7. Scroll to new frame
    figma.viewport.scrollAndZoomIntoView([parentFrame]);

    figma.ui.postMessage({
      type: "done",
      text: `${payload.products.length} slide(s) generated — frame "${payload.frame_name}"`,
    });
  } catch (err) {
    figma.ui.postMessage({ type: "error", text: err.message });
  }
};
