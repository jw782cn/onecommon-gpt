from abc import ABC, abstractmethod
from collections import defaultdict
import numpy as np
import datasets
import evaluate
import oc.bitutils as bitutils
import pdb

class Recall(evaluate.Metric):
    def _info(self):
        return evaluate.MetricInfo(
            description="",
            citation="",
            inputs_description="",
            features=datasets.Features(
                {
                    "predictions": datasets.Sequence(datasets.Sequence(datasets.Value("bool"))),
                    "references": datasets.Sequence(datasets.Sequence(datasets.Value("bool"))),
                }
                if self.config_name == "multilabel"
                else {
                    "predictions": datasets.Sequence(datasets.Value("bool")),
                    "references": datasets.Sequence(datasets.Value("bool")),
                }
            ),
            reference_urls=["https://scikit-learn.org/stable/modules/generated/sklearn.metrics.recall_score.html"],
        )

    def _compute(
        self,
        predictions,
        references,
        labels=None,
        pos_label=1,
        average="sample",
        sample_weight=None,
        zero_division="warn",
    ):
        # TURN LEVEL
        p = 0
        tp = 0
        num_preds = 0

        collapsed_correct = 0
        collapsed_num = 0

        # DOT LEVEL
        dot_p = 0
        dot_tp = 0
        dot_num_preds = 0
        dot_correct = 0
        dot_num = 0

        references = np.array(references)

        for preds, labels in zip(predictions, references):
            preds = np.array(preds)
            # TURN LEVEL
            p += len(labels)
            num_preds += len(preds)
            tp += (preds == labels).all(-1).sum()

            #collapsed_pred = preds.any(0)
            collapsed_pred = preds[0]
            collapsed_label = labels.any(0)

            collapsed_correct += (collapsed_pred == collapsed_label).all()
            collapsed_num += 1

            # DOT LEVEL
            dot_p += collapsed_label.sum()
            dot_tp += (collapsed_pred & collapsed_label).sum()
            dot_num_preds += collapsed_pred.sum()
            dot_correct += (collapsed_pred == collapsed_label).sum()
            dot_num += 7

        dot_recall = dot_tp / dot_p
        dot_precision = dot_tp / dot_num_preds
        dot_f1 = 2 * dot_recall * dot_precision / (dot_recall + dot_precision)

        return {
            "recall": tp / p,
            "precision": tp / num_preds,
            "collapsed_accuracy": collapsed_correct / collapsed_num,
            "dot_recall": dot_recall,
            "dot_precision": dot_precision,
            "dot_f1": dot_f1,
            "dot_accuracy": dot_correct / dot_num,
        }


class Eval(ABC):
    flags = dict()
    logpath = "evaluation_logs"
    method = None

    def compute(self, agent, data, num_examples=None, run_example=None):
        method = getattr(agent, self.method)
        configs = bitutils.get_configs(128)

        preds = []
        truelabels = []

        if run_example is not None:
            # only run a single example
            data = [ex for ex in data if ex["chat_id"] == run_example]

        for ne, example in enumerate(data[:num_examples]):
            chatid = example["chat_id"]
            scenarioid = example["scenario_id"]
            print(f"Example {ne}")
            print(scenarioid)
            print(chatid)


            view = example["context"]
            turns = example["dialogue"]
            referents = example["all_referents"]
            labels = self.get_labels(example)
            past = []
            example_preds = []
            extras = defaultdict(list)
            for t in range(len(turns)):
                text = turns[t]
                past_turns = turns[:t]
                plan = referents[t]

                input = dict(
                    agent = agent,
                    text = text,
                    past = past,
                    view = view,
                    past_turns = past_turns,
                    plan = plan,
                    info = (scenarioid, chatid),
                )

                pred, past, extra = self.predict(**input)

                label = labels[t]
                #import pdb; pdb.set_trace()
                if self.do_eval(text):
                    print("LABEL")
                    if isinstance(self, Generation):
                        preds.append(pred)
                        truelabels.append(label)
                        example_preds.append(pred)
                        print(label)
                    elif isinstance(self, Resolution):
                        preds.append(pred)
                        truelabels.append([label])
                        example_preds.append(pred)
                        print(np.array(label).nonzero()[0])
                    for k,v in extra.items():
                        extras[k].append(v)

            # LOGGING
            log_entry = dict(
                chat_id = chatid,
                scenario_id = scenarioid,
                view = view.tolist(),
                turns = turns,
                referents = referents,
                labels = labels,
                preds = example_preds,
                past = past,
                agent = example["agent"],
                dot_ids = example["real_ids"],
                partner_dot_ids = example["partner_real_ids"],
                output = example["output"],
                **extras,
            )
            self.save_log(log_entry, method, chatid, example["agent"])

        return self.metric.compute(predictions=preds, references=truelabels, **self.flags)

    @abstractmethod
    def predict(self, x):
        pass

    @abstractmethod
    def get_labels(self, x):
        pass

    @abstractmethod
    def do_eval(self, x):
        pass

    def save_log(self, log, method, id, agent):
        import json
        from pathlib import Path
        path = Path(self.logpath) / method / f"{id}-agent{agent}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w") as f:
            json.dump(log, f)


def collapse_referents(xs):
    ret = np.zeros(7, dtype=bool)
    for x in xs:
        ret |= np.array(x["target"], dtype=bool)
    return ret

class Resolution(Eval):
    #metric = evaluate.load("recall", "multilabel")
    metric = Recall("multilabel")
    flags = dict(average="micro")
    logpath = "resolution_logs"
    method = "refres"

    def predict(self, agent, text, past, view, plan, past_turns, info=None):
        pred, newpast, extra = agent.resolve_reference(text, past, view, info)
        if len(pred) == 0:
            pred = np.zeros((1, 7), dtype=bool)
        pred = pred.tolist()
        return pred, newpast, extra
        intpreds = bitutils.config_to_int(pred)
        out = list(set(intpreds.tolist()))
        if len(out) == 0:
            # fill with no reference
            out = [0]
        return pred, newpast, extra

    def get_labels(self, example):
        referents = example["all_referents"]
        # collapse the referents in each turn
        referents = np.stack([collapse_referents(xs) for xs in referents])
        # final turn is selection. output instead of mentions
        output = np.zeros(7, dtype=bool)
        output[example["output"]] = 1
        #referents[-1] = int(bitutils.config_to_int(output))
        referents[-1] = output
        return referents.tolist()

    def do_eval(self, turn):
        #if "<selection>" in turn:
        #    return False
        return True


class Generation(Eval):
    metric = evaluate.load("bleu")
    logpath = "generation_logs"
    method = "gen"

    def predict(self, agent, text, past, view, plan, past_turns, info=None):
        #plan = agent.plan(past, view, info)
        return agent.generate_text(plan, past_turns, view, info)

    def get_labels(self, example):
        return example["dialogue"]

    def do_eval(self, turn):
        return turn.split()[0] == "You:"


if __name__ == "__main__":
    from oc.ocdata import get_data
    from oc.agent.agent import Agent
    import minichain

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--data", choices=["valid", "train"], default="valid")
    parser.add_argument("--split", default=1, type=int)
    parser.add_argument("--model",
        choices=["gpt-3.5-turbo", "gpt-4"],
        default="gpt-3.5-turbo",
    )
    parser.add_argument("--refres",
        choices=["parsecodegen", "codegen", "mc"],
        default="codegen",
    )
    parser.add_argument("--gen",
        choices=["sc", "scxy", "template", "templateonly"],
        default="template",
    )
    parser.add_argument("--run_refres", action="store_true")
    parser.add_argument("--run_gen", action="store_true")
    parser.add_argument("--num_examples", default=25, type=int)
    parser.add_argument("--run_example", default=None, type=str)
    args = parser.parse_args()

    split = args.split
    refres = args.refres
    gen = args.gen

    train, valid = get_data(args.split)

    data = valid if args.data == "valid" else train

    if args.run_refres:
        with minichain.start_chain(f"logs/eval-res-{refres}-{split}-{args.data}-{args.model}") as backend:
            agent = Agent(backend, refres, gen, args.model)
            evaluator = Resolution()
            evaluator.logpath = f"{evaluator.logpath}/{split}/{args.data}/{args.model}"
            reseval = evaluator.compute(agent, data, args.num_examples, args.run_example)
        print(reseval)

    if args.run_gen:
        with minichain.start_chain(f"logs/eval-gen-{gen}-{split}-{args.data}-{args.model}") as backend:
            agent = Agent(backend, refres, gen, args.model)
            evaluator = Generation()
            evaluator.logpath = f"{evaluator.logpath}/{split}/{args.data}/{args.model}"
            geneval = evaluator.compute(agent, data, args.num_examples, args.run_example)
        print(geneval)

