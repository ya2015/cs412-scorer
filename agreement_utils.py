import sentence_tokenizer
import parsers
import tree_utils
from cmd_utils import log
import cache_utils
# UPdated , make verb "am" to singular_verb_tags

singluar_noun_tags = ('NN', 'NNP')
plural_noun_tags = ('NNS', 'NNPS')
# We manually disambiguate Pronouns
noun_tags = singluar_noun_tags + plural_noun_tags + ('PRP',)
# Bug here
# plural_verb_tags = ('VBZ',)
# singular_verb_tags = ('VBP',)
plural_verb_tags = ('VBP',)
singular_verb_tags = ('VBZ',)

general_verb_tags = ('VBD', 'VB')
verb_tags = singular_verb_tags + plural_verb_tags + general_verb_tags

plural_prop_nouns = ('they', 'we', 'them', 'themselves', 'us', 'those')
singluar_prop_nouns = ('he', 'she', 'i', 'him', 'me', 'myself', 'it')


def check_node_agreement(tree_one, tree_two):
    print("tree1:", tree_one)
    print("tree2:",tree_two)
    # First determine which node is the noun node
    if tree_one.label() in noun_tags and tree_two.label() in noun_tags:
        best_pair = select_best_noun_verb(tree_one, tree_two)
        if best_pair:
            noun_tree, verb_tree = best_pair
        else:
            return False
    elif tree_one.label() in noun_tags:
        noun_tree, verb_tree = tree_one, tree_two
    elif tree_two.label() in noun_tags:
        verb_tree, noun_tree = tree_one, tree_two
    else:
        raise Exception("No noun tree in this agreement pair!")

    if noun_tree.label() in singluar_noun_tags:
        noun_3rd_person = True
        noun_singular = True
    elif noun_tree.label() in plural_noun_tags:
        print("plural_noun_tags:", noun_tree.label())
        noun_3rd_person = True
        noun_singular = False
    # In pronoun siutation and need to disambiguate
    elif noun_tree.label() == "PRP":
        noun_3rd_person = not is_pronoun_first_person(noun_tree)
        noun_singular = is_pronoun_singluar(noun_tree)
    else:
        raise Exception("Received some unrecognized noun tag: %s" % (noun_tree.node,))

    if verb_tree.label() not in verb_tags:
        closest_verb_tree = find_commanding_verb_tree(verb_tree)
        if closest_verb_tree:
            verb_tree = closest_verb_tree[0]

    if not verb_tree.label() in verb_tags:
        raise Exception("No verb in this agrement pair!")
    if verb_tree.label() in singular_verb_tags:
        verb_singular = True
    elif verb_tree.label() in plural_verb_tags:
        verb_singular = False
    else:
        verb_singular = True

    log("Noun: Looks like '%s-%s' is %s (%s)" % (noun_tree[0], noun_tree.label(), 'Singular' if noun_singular else 'Plural', "3rd" if noun_3rd_person else "1st"), 2)
    log("Verb: Looks like '%s-%s' is '%s" % (verb_tree[0], verb_tree.label(), 'Singular' if verb_singular else 'Plural'), 2)
    print("Noun: '%s-%s' is %s (%s)" % (noun_tree[0], noun_tree.label(), 'Singular' if noun_singular else 'Plural', "3rd" if noun_3rd_person else "1st"), 2)
    print("Verb: '%s-%s' is '%s" % (verb_tree[0], verb_tree.label(), 'Singular' if verb_singular else 'Plural'), 2)
    
    noun_1st_person = not noun_3rd_person

    # bug for "am"
    is_vbp = (verb_tree.label() == "VBP" and not verb_tree[0].lower() == "am")
    is_vbz = (verb_tree.label() == "VBZ" or verb_tree[0].lower() == "am")
   
  
   
    # is_vbp = not verb_tree[0].lower() == "am"
    # is_vbz = (verb_tree[0].lower() == "am")
    

    if verb_tree.label() in general_verb_tags:
        
        return True
    elif noun_singular and noun_1st_person and is_vbp:
       
        return True
    elif noun_singular and noun_3rd_person and is_vbz:
      
        return True
    elif not noun_singular and noun_3rd_person and is_vbp:
       
        return True
    else:
        log("DONT LIKE COMBO: %s" % ({"verb_tag": verb_tree.label(), "noun_1st_person": noun_1st_person, "noun_singular": noun_singular},), 2)
        print("Error: %s" % ({"verb":verb_tree, "verb_tag": verb_tree.label(), "noun_1st_person": noun_1st_person, "noun_singular": noun_singular},), 2)
        
        return False


def select_best_noun_verb(tree_one, tree_two):
    # Sometimes neither node directly pointed to in the nsubj
    # dependency information is a verb, in which case we need to
    # go searching for a "nearby verb"
    tree_one_verb = find_commanding_verb_tree(tree_one)
    tree_two_verb = find_commanding_verb_tree(tree_two)
    if not tree_one_verb and not tree_two_verb:
        # Something wrong happened.  We have to noun trees but no
        # verb to pair them with
        return None
    elif tree_one_verb and tree_two_verb:
        tree_one_verb_node, tree_one_steps = tree_one_verb
        tree_two_verb_node, tree_two_steps = tree_two_verb
        if tree_one_steps <= tree_two_steps:
            noun_tree, verb_tree = tree_two, tree_one_verb_node
        else:
            noun_tree, verb_tree = tree_one, tree_two_verb_node
    elif tree_one_verb:
        noun_tree, verb_tree = tree_one_verb[0], tree_two
    else:
        noun_tree, verb_tree = tree_two, tree_two_verb[0]

    return noun_tree, verb_tree


def find_commanding_verb_tree(tree, steps=0):
    log("looking for verb at root: %s" % (tree.label(),), 3)
    if tree.label() in verb_tags:
        return (tree, steps)
    else:
        parent_node = tree.parent()
        if not parent_node:
            return None
        else:
            for sibling in parent_node:
                if sibling.label() in verb_tags:
                    return (sibling, steps + 1)
                elif sibling.label() == "VP":
                    return (list(sibling.subtrees(lambda x: x.label() in verb_tags))[0], steps + 2)
            return find_commanding_verb_tree(parent_node, steps + 1)


def is_pronoun_first_person(tree):
    prop_noun = tree.leaves()[0].lower()
    return prop_noun == "i"


def is_pronoun_singluar(tree):
    prop_noun = tree.leaves()[0].lower()
    return prop_noun in singluar_prop_nouns


def is_sentence_root(tree):
    if not tree.label() in tree_utils.semi_tree_roots:
        return False
    else:
        child_nodes = [c.label() for c in tree]
        return "NP" in child_nodes and "VP" in child_nodes


def shallowest_noun_in_tree(tree):
    tree.subtrees(lambda x: x.label() == "NN" or x.label() == "NNS")


def node_in_tree(tree, value):
    subtrees = list(tree.subtrees(lambda x: value in x))
    return subtrees[0] if len(subtrees) > 0 else None


def parse(text, use_cache=True):
    num_agrees = 0
    num_not_agrees = 0
    num_unsure = 0

    lines = text.split("\n")
    for line in lines:
        sentences = sentence_tokenizer.parse(line, use_cache=use_cache)
        for sentence in sentences:

            line_agreements, line_non_agreements, line_unsure = 0, 0, 0

            # Possession seems to be tricky for the parser, so we fudge
            # a little here
            sentence = sentence.replace("'s", '')
            if sentence and sentence[-1] != ".":
                sentence += "."

            if use_cache:
                cache_rs = cache_utils.cache_get('sub_verb_agreement', sentence)
                if cache_rs:
                    line_agreements, line_non_agreements, line_unsure = cache_rs
                    num_agrees += line_agreements
                    num_not_agrees += line_non_agreements
                    num_unsure += line_unsure
                    continue

            log("Looking for Sub-Verb agreement in '%s'" % (sentence,), 1)
            try:
                tree = parsers.parse(sentence)[0]
                print(tree)
            except Exception as e:
                print(e)
                continue
            dependencies = parsers.dependences(sentence, use_cache=False)
            sub_verb_deps = [dep for dep in dependencies if dep['dep_name'] == 'nsubj']
            # sub_verb_deps = [dep for dep in dependencies]
            if len(sub_verb_deps) == 0:
                log("Couldn't find Subject-Verb dependency info", 1)
                cache_utils.cache_set('sub_verb_agreement', sentence, (0, 0, 0))
                continue

            for sub_verb in sub_verb_deps:
                first_node = node_in_tree(tree, sub_verb['first_word'])
                sec_node = node_in_tree(tree, sub_verb['second_word'])
                if first_node and sec_node:

                    log("First Dep Node: %s" % (first_node,), 2)
                    log("Sec Dep Node: %s" % (sec_node,), 2)

                    try:
                        is_agreement = check_node_agreement(first_node, sec_node)
                        if is_agreement:
                            line_agreements += 1
                        else:
                            line_non_agreements += 1
                        log("Agreement in sentence? %s" % (is_agreement,), 1)
                       
                    except Exception as e:
                        line_unsure += 1
                        log("Error looking for agreement? %s" % (e,), 2)
                       
                        # No agreement in pair.  Not sure how to handle.
                        # More exhaustive search?
            if use_cache:
                cache_utils.cache_set('sub_verb_agreement', sentence, (line_agreements, line_non_agreements, line_unsure))
            num_agrees += line_agreements
            num_not_agrees += line_non_agreements
            num_unsure += line_unsure

    return num_agrees, num_not_agrees, num_unsure
